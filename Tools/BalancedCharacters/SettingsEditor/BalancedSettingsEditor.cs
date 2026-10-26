using System;
using System.Collections.Generic;
using System.Collections;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

public sealed class GeneralSettings
{
    [Category("Collection"), DisplayName("Unlock all cards")]
    public bool UnlockAllCards { get; set; }
    [Category("Collection"), DisplayName("Unlock all items")]
    public bool UnlockAllItems { get; set; }
    [Category("Collection"), DisplayName("Allow crafting all cards")]
    public bool CardCraftableAll { get; set; }
    [Category("Collection"), DisplayName("Allow dismantling restricted cards")]
    public bool DisableNoDismantle { get; set; }
    [Category("New players"), DisplayName("Starting gems"), Description("Applies when a player is created; existing balances are preserved.")]
    public int DefaultGems { get; set; }
    [Category("Standard campaign rewards"), DisplayName("New chapter reward multiplier")]
    public double ChapterRewardMultiplier { get; set; }
    [Category("Standard campaign rewards"), DisplayName("Win gems minimum")]
    public int WinMin { get; set; }
    [Category("Standard campaign rewards"), DisplayName("Win gems maximum")]
    public int WinMax { get; set; }
    [Category("Standard campaign rewards"), DisplayName("Loss gems minimum")]
    public int LoseMin { get; set; }
    [Category("Standard campaign rewards"), DisplayName("Loss gems maximum")]
    public int LoseMax { get; set; }
}

/// <summary>A compiled Balanced deck set in Data/BalancedCharacters/Revisions/&lt;revision&gt;.</summary>
public sealed class DeckSet
{
    public string Revision, Description, Folder, ContentVersion;
    public List<string> CharacterIds;
    public override string ToString() { return Revision + " - " + Description; }

    public static List<DeckSet> Find(string modeRoot)
    {
        var result = new List<DeckSet>();
        string dir = Path.Combine(modeRoot, "Revisions");
        if (!Directory.Exists(dir)) return result;
        var json = new JavaScriptSerializer();
        foreach (string folder in Directory.GetDirectories(dir).OrderBy(x => x, StringComparer.OrdinalIgnoreCase))
        {
            string packFile = Path.Combine(folder, "Pack.json");
            if (!File.Exists(packFile)) continue;
            var pack = json.Deserialize<Dictionary<string, object>>(File.ReadAllText(packFile));
            var set = new DeckSet {
                Revision = (string)pack["revision"], Description = (string)pack["description"], Folder = folder,
                ContentVersion = (string)pack["contentVersion"],
                CharacterIds = ((IList)pack["activeCharacterIds"]).Cast<object>().Select(x => (string)x).ToList() };
            if (set.Revision != Path.GetFileName(folder) || set.CharacterIds.Count < 2 ||
                !Directory.Exists(Path.Combine(modeRoot, "Decks", set.Revision)) ||
                DeckSet.Files.Any(f => !File.Exists(Path.Combine(folder, f))))
                continue; // incomplete pack: not offered
            result.Add(set);
        }
        return result;
    }

    // Pack file -> where it goes in the runtime (relative to the runtime root)
    public static readonly string[] Files = { "Overlay.json", "SoloGateCards.txt", "IDS_BALANCED_CHARACTERS.txt" };
    public static string Target(string root, string file)
    {
        if (file == "IDS_BALANCED_CHARACTERS.txt") return Path.Combine(root, "Data", "ClientData", "IDS", file);
        return Path.Combine(root, "Data", "BalancedCharacters", "Generated", file);
    }
}

public sealed class EditorDocument
{
    public readonly string Root, SettingsPath, ModePath;
    public readonly GeneralSettings Values = new GeneralSettings();
    public bool Enabled;
    public readonly List<DeckSet> DeckSets;
    public string CurrentRevision { get; private set; }
    public string SelectedRevision;
    public readonly List<string> LoadedSets = new List<string>();
    string originalSettings, originalMode;
    Dictionary<string, object> settings, mode;
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    static Dictionary<string, object> Object(object value) { return (Dictionary<string, object>)value; }
    static Dictionary<string, object> Read(string text) { return Json.Deserialize<Dictionary<string, object>>(text); }
    static IList Array(object value) { return (IList)value; }
    Dictionary<string, object> Rewards { get { return Object(settings["DuelRewards"]); } }
    Dictionary<string, object> Win { get { return Object(Array(Rewards["win"])[4]); } }
    Dictionary<string, object> Lose { get { return Object(Array(Rewards["lose"])[0]); } }
    public EditorDocument(string root)
    {
        Root = Path.GetFullPath(root);
        SettingsPath = Path.Combine(Root, "Data", "Settings.json");
        ModePath = Path.Combine(Root, "Data", "BalancedCharacters", "Mode.json");
        originalSettings = File.ReadAllText(SettingsPath); originalMode = File.ReadAllText(ModePath);
        settings = Read(originalSettings); mode = Read(originalMode);
        if (Convert.ToInt32(mode["schemaVersion"]) != 1) throw new InvalidDataException("Unsupported balanced-mode schema.");
        Enabled = Convert.ToBoolean(mode["enabled"]);
        CurrentRevision = mode.ContainsKey("activeDeckRevision") ? (string)mode["activeDeckRevision"] : "source-v1";
        SelectedRevision = CurrentRevision;
        DeckSets = DeckSet.Find(Path.GetDirectoryName(ModePath));
        // Deck sets the game loads at once, each in its own Stories folder (Mode.json "sets").
        if (mode.ContainsKey("sets") && mode["sets"] is IList)
            foreach (var entry in Array(mode["sets"]).OfType<Dictionary<string, object>>())
                if (entry.ContainsKey("revision")) LoadedSets.Add((string)entry["revision"]);
        if ((string)Win["type"] != "Gem" || (string)Lose["type"] != "Gem")
            throw new InvalidDataException("Unexpected reward layout. Original settings preserved.");
        Values.UnlockAllCards = Convert.ToBoolean(settings["UnlockAllCards"]);
        Values.UnlockAllItems = Convert.ToBoolean(settings["UnlockAllItems"]);
        Values.CardCraftableAll = Convert.ToBoolean(settings["CardCraftableAll"]);
        Values.DisableNoDismantle = Convert.ToBoolean(settings["DisableNoDismantle"]);
        Values.DefaultGems = Convert.ToInt32(settings["DefaultGems"]);
        Values.ChapterRewardMultiplier = Convert.ToDouble(Rewards["ChapterStatusChangedMultiplier"]);
        Values.WinMin = Convert.ToInt32(Win["min"]); Values.WinMax = Convert.ToInt32(Win["max"]);
        Values.LoseMin = Convert.ToInt32(Lose["min"]); Values.LoseMax = Convert.ToInt32(Lose["max"]);
    }
    public void Validate()
    {
        if (Values.DefaultGems < 0 || Values.WinMin < 0 || Values.LoseMin < 0 ||
            Values.WinMax < Values.WinMin || Values.LoseMax < Values.LoseMin ||
            double.IsNaN(Values.ChapterRewardMultiplier) || double.IsInfinity(Values.ChapterRewardMultiplier) ||
            Values.ChapterRewardMultiplier < 0)
            throw new InvalidDataException("Use nonnegative values and maximum rewards at least equal to their minimum.");
    }
    public void Save()
    {
        Validate();
        if (File.ReadAllText(SettingsPath) != originalSettings || File.ReadAllText(ModePath) != originalMode)
            throw new IOException("Settings changed outside this editor. Close and reopen it before saving.");
        settings["UnlockAllCards"] = Values.UnlockAllCards; settings["UnlockAllItems"] = Values.UnlockAllItems;
        settings["CardCraftableAll"] = Values.CardCraftableAll; settings["DisableNoDismantle"] = Values.DisableNoDismantle;
        settings["DefaultGems"] = Values.DefaultGems;
        Rewards["ChapterStatusChangedMultiplier"] = Values.ChapterRewardMultiplier;
        Win["min"] = Values.WinMin; Win["max"] = Values.WinMax;
        Lose["min"] = Values.LoseMin; Lose["max"] = Values.LoseMax;
        mode["enabled"] = Enabled;
        // Deck set switch: the chosen pack's compiled overlay, gate thumbnails and texts go into
        // place, and Mode.json names its revision, characters and content version.
        DeckSet switchTo = null;
        if (SelectedRevision != CurrentRevision)
        {
            switchTo = DeckSets.FirstOrDefault(x => x.Revision == SelectedRevision);
            if (switchTo == null) throw new InvalidDataException("Deck set " + SelectedRevision + " is not installed.");
            mode["activeDeckRevision"] = switchTo.Revision;
            mode["activeCharacterIds"] = switchTo.CharacterIds.ToArray();
            mode["contentVersion"] = switchTo.ContentVersion;
        }
        string newSettings = Json.Serialize(settings), newMode = Json.Serialize(mode);
        string stamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6);
        string settingsBackup = SettingsPath + ".before-balanced-editor-" + stamp + ".bak";
        string modeBackup = ModePath + ".before-balanced-editor-" + stamp + ".bak";
        // Deck set files are backed up under EditorBackups: the client loads every file in
        // Data/ClientData/IDS, so a backup next to the texts would override them.
        string packBackupDir = Path.Combine(Root, "EditorBackups", "deck-set-" + stamp);
        Read(newSettings); Read(newMode);
        File.Copy(SettingsPath, settingsBackup);
        File.Copy(ModePath, modeBackup);
        var originalPackFiles = new Dictionary<string, byte[]>();
        if (switchTo != null)
        {
            Directory.CreateDirectory(packBackupDir);
            foreach (string file in DeckSet.Files)
            {
                string target = DeckSet.Target(Root, file);
                if (File.Exists(target))
                {
                    originalPackFiles[target] = File.ReadAllBytes(target);
                    File.Copy(target, Path.Combine(packBackupDir, file));
                }
            }
        }
        try
        {
            File.WriteAllText(SettingsPath, newSettings, new UTF8Encoding(false));
            if (switchTo != null)
                foreach (string file in DeckSet.Files)
                    File.Copy(Path.Combine(switchTo.Folder, file), DeckSet.Target(Root, file), true);
            File.WriteAllText(ModePath, newMode, new UTF8Encoding(false));
            if (File.ReadAllText(SettingsPath) != newSettings || File.ReadAllText(ModePath) != newMode)
                throw new IOException("Saved settings did not match the requested values.");
            originalSettings = newSettings; originalMode = newMode;
            if (switchTo != null) CurrentRevision = switchTo.Revision;
        }
        catch (Exception saveError)
        {
            try
            {
                File.WriteAllText(SettingsPath, originalSettings, new UTF8Encoding(false));
                File.WriteAllText(ModePath, originalMode, new UTF8Encoding(false));
                foreach (var pair in originalPackFiles) File.WriteAllBytes(pair.Key, pair.Value);
            }
            catch (Exception restoreError)
            {
                throw new AggregateException("Save failed. Restore the .before-balanced-editor backups before continuing.", saveError, restoreError);
            }
            throw;
        }
    }
    public static void CheckRuntime(string root)
    {
        new EditorDocument(root).Validate();
        foreach (string relative in new [] { "YgoMaster.exe", "YgoMasterClient.exe", "Data/ClientData/ClientSettings.json" })
            if (!File.Exists(Path.Combine(root, relative))) throw new FileNotFoundException("Missing runtime file: " + relative);
    }
    public static void SelfTest(string root)
    {
        // Run only against the disposable fixture explicitly supplied by the test command.
        var d = new EditorDocument(root);
        var oldSettings = Read(File.ReadAllText(d.SettingsPath));
        var oldMode = Read(File.ReadAllText(d.ModePath));
        int oldGems = d.Values.DefaultGems; bool oldEnabled = d.Enabled;
        d.Values.DefaultGems = oldGems + 1; d.Enabled = !oldEnabled; d.Save();
        var again = new EditorDocument(root);
        if (again.Values.DefaultGems != oldGems + 1 || again.Enabled == oldEnabled) throw new Exception("Edited fields did not persist.");
        var nowSettings = Read(File.ReadAllText(d.SettingsPath)); nowSettings["DefaultGems"] = oldGems;
        var nowMode = Read(File.ReadAllText(d.ModePath)); nowMode["enabled"] = oldEnabled;
        if (!Equivalent(oldSettings, nowSettings) || !Equivalent(oldMode, nowMode))
            throw new Exception("An unrelated field changed.");
        if (Directory.GetFiles(Path.GetDirectoryName(d.SettingsPath), "*.before-balanced-editor-*.bak").Length < 1)
            throw new Exception("Settings backup missing.");
        var conflict = new EditorDocument(root);
        File.AppendAllText(conflict.SettingsPath, " ");
        bool rejected = false;
        try { conflict.Save(); } catch (IOException) { rejected = true; }
        if (!rejected) throw new Exception("Concurrent change was overwritten.");
        again.Values.WinMin = again.Values.WinMax + 1;
        bool invalid = false;
        try { again.Validate(); } catch (InvalidDataException) { invalid = true; }
        if (!invalid) throw new Exception("Invalid reward range accepted.");
        Console.WriteLine("PASS save/reload, unrelated keys and ports, balanced defaults, backups, concurrent edit rejection, reward validation");

        // Deck set switching (needs at least two installed packs)
        var fresh = new EditorDocument(root);
        if (fresh.DeckSets.Count < 2) { Console.WriteLine("SKIP deck set switching: fewer than two packs installed"); return; }
        string start = fresh.CurrentRevision;
        string idsDir = Path.Combine(root, "Data", "ClientData", "IDS");
        int idsFiles = Directory.GetFiles(idsDir).Length;
        foreach (var target in fresh.DeckSets.Where(x => x.Revision != start).Concat(fresh.DeckSets.Where(x => x.Revision == start)))
        {
            var doc = new EditorDocument(root);
            doc.SelectedRevision = target.Revision;
            doc.Save();
            var m = Read(File.ReadAllText(doc.ModePath));
            if ((string)m["activeDeckRevision"] != target.Revision || (string)m["contentVersion"] != target.ContentVersion ||
                !((IList)m["activeCharacterIds"]).Cast<object>().Select(x => (string)x).SequenceEqual(target.CharacterIds))
                throw new Exception("Mode.json does not name deck set " + target.Revision);
            foreach (string file in DeckSet.Files)
                if (!File.ReadAllBytes(DeckSet.Target(root, file)).SequenceEqual(File.ReadAllBytes(Path.Combine(target.Folder, file))))
                    throw new Exception(file + " was not switched to " + target.Revision);
            if (Directory.GetFiles(idsDir).Length != idsFiles) throw new Exception("Extra files were left in Data/ClientData/IDS.");
            Console.WriteLine("PASS switched deck set to " + target.Revision);
        }
        if (!Directory.GetDirectories(Path.Combine(root, "EditorBackups"), "deck-set-*").Any())
            throw new Exception("Deck set backup missing.");
        Console.WriteLine("PASS deck set switching, backups under EditorBackups, switched back to " + start);
    }
    static bool Equivalent(object a, object b)
    {
        var da = a as Dictionary<string, object>; var db = b as Dictionary<string, object>;
        if (da != null || db != null)
            return da != null && db != null && da.Count == db.Count && da.All(pair => db.ContainsKey(pair.Key) && Equivalent(pair.Value, db[pair.Key]));
        var la = a as IList; var lb = b as IList;
        if (la != null || lb != null)
            return la != null && lb != null && la.Count == lb.Count && Enumerable.Range(0, la.Count).All(i => Equivalent(la[i], lb[i]));
        if (a is string || b is string || a is bool || b is bool || a == null || b == null) return Equals(a, b);
        return Convert.ToDecimal(a) == Convert.ToDecimal(b);
    }
}

/// <summary>Theme colors for the editor window.</summary>
static class Theme
{
    public static readonly Color Panel = Color.FromArgb(215, 14, 18, 30);
    public static readonly Color PanelSoft = Color.FromArgb(185, 20, 26, 42);
    public static readonly Color Accent = Color.FromArgb(214, 232, 40);      // Master Duel lime
    public static readonly Color AccentDark = Color.FromArgb(120, 135, 20);
    public static readonly Color Text = Color.FromArgb(235, 238, 245);
    public static readonly Color Muted = Color.FromArgb(160, 170, 190);
    public static readonly Color Field = Color.FromArgb(28, 34, 52);
    public static readonly Color Line = Color.FromArgb(55, 64, 92);
}

/// <summary>A card-style panel: translucent dark fill with a thin accent line on top.</summary>
sealed class CardPanel : Panel
{
    public CardPanel() { DoubleBuffered = true; BackColor = Theme.Panel; Padding = new Padding(14, 12, 14, 12); }
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using (var pen = new Pen(Theme.Accent, 2)) e.Graphics.DrawLine(pen, 0, 1, Width, 1);
    }
}

public sealed class BalancedEditorForm : Form
{
    readonly EditorDocument document;
    readonly CheckBox enabled;
    readonly ComboBox deckSet;
    readonly Label status, setDescription, setCharacters;
    readonly PropertyGrid grid;
    Button startButton, hostButton, joinButton;
    Image background;

    public BalancedEditorForm(string root)
    {
        document = new EditorDocument(root);
        Text = "Start Game - Yu-Gi-Oh! Master Duel (Balanced Characters)";
        StartPosition = FormStartPosition.CenterScreen; Size = new Size(1060, 760); MinimumSize = new Size(920, 680);
        Font = new Font("Segoe UI", 10); ForeColor = Theme.Text; BackColor = Color.FromArgb(10, 12, 20);
        DoubleBuffered = true;
        string bg = Path.Combine(document.Root, "Data", "ClientData", "CustomBackground.png");
        if (File.Exists(bg)) { using (var tmp = Image.FromFile(bg)) background = new Bitmap(tmp); }

        var outer = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 3, Padding = new Padding(18), BackColor = Color.Transparent };
        outer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 46));
        outer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 54));
        outer.RowStyles.Add(new RowStyle(SizeType.Absolute, 96));
        outer.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        outer.RowStyles.Add(new RowStyle(SizeType.Absolute, 92));
        Controls.Add(outer);

        // Header
        var header = new CardPanel { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 12) };
        outer.Controls.Add(header, 0, 0); outer.SetColumnSpan(header, 2);
        header.Controls.Add(new Label { Text = "BALANCED CHARACTERS", Font = new Font("Segoe UI Semibold", 20), ForeColor = Theme.Accent, AutoSize = true, Location = new Point(14, 8), BackColor = Color.Transparent });
        header.Controls.Add(new Label { Text = document.Root, ForeColor = Theme.Muted, AutoSize = true, Location = new Point(17, 50), BackColor = Color.Transparent, Font = new Font("Segoe UI", 9) });
        enabled = new CheckBox { Text = "Enable Balanced Character Duels", Checked = document.Enabled, AutoSize = true, ForeColor = Theme.Text, BackColor = Color.Transparent, Font = new Font("Segoe UI Semibold", 10.5f), Anchor = AnchorStyles.Top | AnchorStyles.Right };
        header.Controls.Add(enabled);
        header.Layout += (s, e) => enabled.Location = new Point(header.Width - enabled.Width - 18, 30);

        // Left column: deck set and its characters
        var setCard = new CardPanel { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 12, 0) };
        outer.Controls.Add(setCard, 0, 1);
        setCard.Controls.Add(SectionTitle("STORIES MODES", 14, 10));
        deckSet = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Location = new Point(16, 40), Width = 380, BackColor = Theme.Field, ForeColor = Theme.Text, FlatStyle = FlatStyle.Flat, Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
        // Every loaded deck set is its own mode in SOLO > Stories; this list only shows them (nothing to switch).
        var loaded = document.LoadedSets.Count > 0 ? document.LoadedSets : new List<string> { document.CurrentRevision };
        foreach (string revision in loaded)
        {
            var set = document.DeckSets.FirstOrDefault(x => x.Revision == revision);
            if (set != null) deckSet.Items.Add(new ModeItem(set));
        }
        if (deckSet.Items.Count > 0) deckSet.SelectedIndex = 0;
        else { deckSet.Items.Add("(no deck sets installed)"); deckSet.SelectedIndex = 0; deckSet.Enabled = false; }
        setCard.Controls.Add(deckSet);
        setDescription = new Label { Location = new Point(16, 78), AutoSize = false, Size = new Size(380, 48), ForeColor = Theme.Text, BackColor = Color.Transparent, Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
        setCard.Controls.Add(setDescription);
        setCharacters = new Label { Location = new Point(16, 162), AutoSize = false, Size = new Size(380, 300), ForeColor = Theme.Text, BackColor = Color.Transparent, Font = new Font("Segoe UI", 10.5f), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom };
        setCard.Controls.Add(new Label { Text = "CHARACTERS IN THIS SET", Location = new Point(14, 134), AutoSize = true, ForeColor = Theme.Muted, BackColor = Color.Transparent, Font = new Font("Segoe UI Semibold", 9) });
        setCard.Controls.Add(setCharacters);
        setCard.Layout += (s, e) => { int w = setCard.Width - 32; deckSet.Width = w; setDescription.Width = w; setCharacters.Width = w; setCharacters.Height = Math.Max(60, setCard.Height - 176); };
        deckSet.SelectedIndexChanged += (s, e) => ShowSet();

        // Right column: settings
        var settingsCard = new CardPanel { Dock = DockStyle.Fill };
        outer.Controls.Add(settingsCard, 1, 1);
        settingsCard.Controls.Add(SectionTitle("SETTINGS", 14, 10));
        grid = new PropertyGrid {
            SelectedObject = document.Values, ToolbarVisible = false, HelpVisible = true, Location = new Point(14, 40),
            Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
            ViewBackColor = Theme.Field, ViewForeColor = Theme.Text, LineColor = Theme.Line, CategoryForeColor = Theme.Accent,
            CategorySplitterColor = Theme.Line, HelpBackColor = Color.FromArgb(22, 27, 42), HelpForeColor = Theme.Muted,
            BackColor = Color.FromArgb(22, 27, 42), ViewBorderColor = Theme.Line, HelpBorderColor = Theme.Line,
            CommandsBackColor = Theme.Field, SelectedItemWithFocusBackColor = Theme.AccentDark, SelectedItemWithFocusForeColor = Color.White };
        settingsCard.Controls.Add(grid);
        settingsCard.Layout += (s, e) => grid.Size = new Size(settingsCard.Width - 28, settingsCard.Height - 54);

        // Footer: info, buttons, status
        var footer = new CardPanel { Dock = DockStyle.Fill, Margin = new Padding(0, 12, 0, 0), BackColor = Theme.PanelSoft };
        outer.Controls.Add(footer, 0, 2); outer.SetColumnSpan(footer, 2);
        var buttons = new FlowLayoutPanel { Location = new Point(12, 10), AutoSize = true, WrapContents = false, BackColor = Color.Transparent };
        footer.Controls.Add(buttons);
        startButton = AddButton(buttons, "Start Game", true, () => StartGame());
        hostButton = AddButton(buttons, "Host a server", false, () => HostGame());
        joinButton = AddButton(buttons, "Join a server", false, () => JoinGame());
        AddButton(buttons, "Save", false, () => Save());
        AddButton(buttons, "Close", false, () => Close());
        status = new Label { Location = new Point(16, 56), AutoSize = true, ForeColor = Theme.Muted, BackColor = Color.Transparent,
            Text = "Start Game saves your settings, then starts the server and Master Duel." };
        try { GameLauncher.HideSupportFiles(document.Root); } catch { }
        footer.Controls.Add(status);
        ShowSet();
    }

    protected override void OnPaintBackground(PaintEventArgs e)
    {
        if (background == null) { base.OnPaintBackground(e); return; }
        // Cover the window with the image, then darken it so the panels stay readable.
        float scale = Math.Max((float)ClientSize.Width / background.Width, (float)ClientSize.Height / background.Height);
        int w = (int)(background.Width * scale), h = (int)(background.Height * scale);
        e.Graphics.DrawImage(background, (ClientSize.Width - w) / 2, (ClientSize.Height - h) / 2, w, h);
        using (var shade = new SolidBrush(Color.FromArgb(120, 5, 6, 12))) e.Graphics.FillRectangle(shade, ClientRectangle);
    }
    protected override void OnResize(EventArgs e) { base.OnResize(e); Invalidate(); }

    static Label SectionTitle(string text, int x, int y)
    {
        return new Label { Text = text, Location = new Point(x, y), AutoSize = true, ForeColor = Theme.Accent, BackColor = Color.Transparent, Font = new Font("Segoe UI Semibold", 10.5f) };
    }

    static Button MakeButton(string text, bool primary)
    {
        var b = new Button { Text = text, AutoSize = true, Height = 36, Padding = new Padding(10, 0, 10, 0), FlatStyle = FlatStyle.Flat,
            BackColor = primary ? Theme.Accent : Theme.Field, ForeColor = primary ? Color.FromArgb(15, 18, 10) : Theme.Text,
            Font = new Font("Segoe UI Semibold", 10), Cursor = Cursors.Hand, Margin = new Padding(0, 0, 10, 0) };
        b.FlatAppearance.BorderColor = primary ? Theme.Accent : Theme.Line;
        b.FlatAppearance.MouseOverBackColor = primary ? Color.FromArgb(235, 250, 90) : Theme.Line;
        return b;
    }

    Button AddButton(FlowLayoutPanel panel, string text, bool primary, Action action)
    {
        var button = MakeButton(text, primary);
        button.Click += (s, e) => { try { action(); } catch (Exception ex) { ShowError(ex.Message); } };
        panel.Controls.Add(button);
        return button;
    }

    void ShowError(string message)
    {
        status.Text = message;
        MessageBox.Show(this, message, "Start Game", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }

    /// <summary>A Stories mode in the list: the deck set and the folder name it has in the game.</summary>
    sealed class ModeItem
    {
        public readonly DeckSet Set;
        public ModeItem(DeckSet set) { Set = set; }
        public static string ModeName(string revision)
        {
            switch (revision)
            {
                case "source-v2": return "Balanced Characters";
                case "source-v3": return "Goat Era Duelists";
                case "source-v4": return "Duel Royale";
                case "source-v5": return "Goat Format Strategies";
                case "source-v6": return "Edison Format Strategies";
                default: return revision;
            }
        }
        public override string ToString() { return ModeName(Set.Revision) + "  (" + Set.CharacterIds.Count + " decks)"; }
    }

    DeckSet SelectedSet() { var item = deckSet.SelectedItem as ModeItem; return item == null ? null : item.Set; }

    void ShowSet()
    {
        var set = SelectedSet();
        if (set == null) { setDescription.Text = ""; setCharacters.Text = ""; return; }
        setDescription.Text = set.Description + "   (SOLO > Stories > " + ModeItem.ModeName(set.Revision) + ")";
        setCharacters.Text = string.Join("\n", CharacterNames(set).Select(n => "•  " + n));
    }

    /// <summary>Display names of a set's characters, from its Pack.json.</summary>
    static List<string> CharacterNames(DeckSet set)
    {
        var pack = new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(Path.Combine(set.Folder, "Pack.json")));
        var names = pack.ContainsKey("characters") ? ((IList)pack["characters"]).Cast<object>().Select(x => (string)x).ToList() : new List<string>();
        return set.CharacterIds.Select((id, i) => i < names.Count ? names[i] : id).ToList();
    }

    void Save()
    {
        ValidateChildren();
        document.Enabled = enabled.Checked;
        document.Save();
        ShowSet();
        status.Text = "Saved with backups. Other settings and saves preserved.";
    }

    void StartGame() { Launch(GameLauncher.NetMode.Offline, null); }

    /// <summary>Host a server: pick this PC's network address, then start the open server and the game.</summary>
    void HostGame()
    {
        var addresses = GameLauncher.LocalAddresses();
        string saved = GameLauncher.SavedServerAddress(document.Root);
        if (saved.Length > 0 && addresses.Contains(saved)) { addresses.Remove(saved); addresses.Insert(0, saved); }
        string address = AskAddress("Host a server",
            "Pick this PC's address on the network you share with the other players.\n" +
            "Tailscale and ZeroTier addresses (100.x) and Radmin VPN (26.x) are listed first.\n" +
            "Tell the other players this address; they press Join a server and enter it.", addresses, true);
        if (address == null) return;
        if (!GameLauncher.IsAdministrator())
        {
            var answer = MessageBox.Show(this, "Windows only lets a program accept connections from other PCs when it runs as administrator.\n\n" +
                "Restart Start Game as administrator and host on " + address + "?\n(Windows will ask you to confirm.)",
                "Host a server", MessageBoxButtons.YesNo, MessageBoxIcon.Information);
            if (answer != DialogResult.Yes) return;
            Save();
            try
            {
                Process.Start(new ProcessStartInfo(Application.ExecutablePath, "--host \"" + address + "\" \"" + document.Root.TrimEnd('\\') + "\"") { UseShellExecute = true, Verb = "runas" });
                Close();
            }
            catch (System.ComponentModel.Win32Exception) { status.Text = "Hosting cancelled (administrator rights were not given)."; }
            return;
        }
        Launch(GameLauncher.NetMode.Host, address);
    }

    /// <summary>Join a server: enter the host's address, then start only the game, connected to it.</summary>
    void JoinGame()
    {
        string saved = GameLauncher.SavedServerAddress(document.Root);
        string address = AskAddress("Join a server",
            "Enter the address the host gave you (shown in their Host a server window).\n" +
            "You both need the same private network app (Tailscale, ZeroTier or Radmin VPN) running.",
            saved.Length > 0 ? new List<string> { saved } : new List<string>(), false);
        if (address == null) return;
        Launch(GameLauncher.NetMode.Join, address);
    }

    /// <summary>Saves settings, applies the network mode and starts the game (with or without a local server).</summary>
    internal void Launch(GameLauncher.NetMode mode, string address)
    {
        if (Process.GetProcessesByName("masterduel").Length > 0)
            throw new InvalidOperationException("Master Duel is already running. Close it first, then try again.");
        Save();
        GameLauncher.ApplyNetwork(document.Root, mode, address);
        GameLauncher.Validate(document.Root);
        startButton.Enabled = hostButton.Enabled = joinButton.Enabled = false;
        status.Text = mode == GameLauncher.NetMode.Join ? "Connecting..." : "Starting the server...";
        Cursor = Cursors.AppStarting;
        string root = document.Root;
        var worker = new System.Threading.Thread(() =>
        {
            try
            {
                Action<string> progress = text => BeginInvoke((Action)(() => status.Text = text));
                string message = mode == GameLauncher.NetMode.Join
                    ? GameLauncher.StartClientOnly(root, address, progress)
                    : GameLauncher.Start(root, progress);
                if (mode == GameLauncher.NetMode.Host)
                {
                    BeginInvoke((Action)(() => MessageBox.Show(this, "Your server is open on " + address + ".\n\nTell the other players to press Join a server and enter:\n" + address +
                        "\n\nKeep this PC on while they play. If Windows asks whether YgoMaster may use the network, choose Allow.",
                        "Hosting", MessageBoxButtons.OK, MessageBoxIcon.Information)));
                }
                BeginInvoke((Action)(() => { status.Text = message; Close(); }));
            }
            catch (Exception ex)
            {
                GameLauncher.LogError(root, ex.Message);
                BeginInvoke((Action)(() => { Cursor = Cursors.Default; startButton.Enabled = hostButton.Enabled = joinButton.Enabled = true; ShowError(ex.Message + "\n\nDetails are in the LaunchLogs folder."); }));
            }
        }) { IsBackground = true };
        worker.Start();
    }

    /// <summary>Small themed dialog with a list of addresses (or a text box when editable). Returns null on Cancel.</summary>
    string AskAddress(string title, string text, List<string> choices, bool pickFromList)
    {
        using (var dialog = new Form { Text = title, FormBorderStyle = FormBorderStyle.FixedDialog, MaximizeBox = false, MinimizeBox = false,
            StartPosition = FormStartPosition.CenterParent, ClientSize = new Size(520, 210), BackColor = Color.FromArgb(18, 22, 36), ForeColor = Theme.Text, Font = Font })
        {
            dialog.Controls.Add(new Label { Text = text, Location = new Point(18, 14), Size = new Size(484, 72), ForeColor = Theme.Text });
            var box = new ComboBox { Location = new Point(18, 94), Width = 484, BackColor = Theme.Field, ForeColor = Theme.Text, FlatStyle = FlatStyle.Flat,
                DropDownStyle = pickFromList && choices.Count > 0 ? ComboBoxStyle.DropDown : ComboBoxStyle.Simple, Height = 30 };
            foreach (string c in choices) box.Items.Add(c);
            if (choices.Count > 0) box.Text = choices[0];
            dialog.Controls.Add(box);
            var ok = MakeButton(pickFromList ? "Host" : "Join", true); ok.Location = new Point(300, 150); ok.DialogResult = DialogResult.OK;
            var cancel = MakeButton("Cancel", false); cancel.Location = new Point(410, 150); cancel.DialogResult = DialogResult.Cancel;
            dialog.Controls.Add(ok); dialog.Controls.Add(cancel);
            dialog.AcceptButton = ok; dialog.CancelButton = cancel;
            if (pickFromList && choices.Count == 0)
                dialog.Controls.Add(new Label { Text = "No network address found: start your private network app first.", Location = new Point(18, 126), AutoSize = true, ForeColor = Theme.Muted });
            if (dialog.ShowDialog(this) != DialogResult.OK) return null;
            string value = box.Text.Trim();
            if (value.Length == 0) { ShowError("Enter an address."); return null; }
            return value;
        }
    }
}

/// <summary>
/// Starts the balanced server and Master Duel client (what Start-Balanced.ps1 used to do):
/// checks ports and paths, restarts only this folder's own server, waits for its ports, then starts the client.
/// </summary>
static class GameLauncher
{
    /// <summary>Files and folders that players never need to open; hidden so Start Game.exe stands out.</summary>
    public static readonly string[] SupportItems = { "YgoMaster.exe", "YgoMaster.exe.config", "YgoMasterClient.exe",
        "YgoMasterClient.exe.config", "YgoMasterLoader.dll", "Stop-Balanced.ps1", "SoloThumbnailFix.log",
        "LaunchLogs", "EditorBackups", "UpgradeBackups" };

    public static void HideSupportFiles(string root)
    {
        foreach (string name in SupportItems)
        {
            string path = Path.Combine(root, name);
            if (File.Exists(path) || Directory.Exists(path))
            {
                var attributes = File.GetAttributes(path);
                if ((attributes & FileAttributes.Hidden) == 0) File.SetAttributes(path, attributes | FileAttributes.Hidden);
            }
        }
    }

    /// <summary>Settings files allow // comments and trailing commas; strip them outside strings.</summary>
    static Dictionary<string, object> ReadLoose(string path)
    {
        string source = File.ReadAllText(path);
        var clean = new StringBuilder();
        bool quoted = false, escaped = false;
        for (int i = 0; i < source.Length; i++)
        {
            char c = source[i];
            if (quoted)
            {
                clean.Append(c);
                if (escaped) escaped = false; else if (c == '\\') escaped = true; else if (c == '"') quoted = false;
                continue;
            }
            if (c == '"') { quoted = true; clean.Append(c); continue; }
            if (c == '/' && i + 1 < source.Length && source[i + 1] == '/') { while (i < source.Length && source[i] != '\n') i++; clean.Append('\n'); continue; }
            if (c == '/' && i + 1 < source.Length && source[i + 1] == '*') { i += 2; while (i + 1 < source.Length && !(source[i] == '*' && source[i + 1] == '/')) i++; i++; continue; }
            if (c == ',')
            {
                int next = i + 1;
                while (next < source.Length && char.IsWhiteSpace(source[next])) next++;
                if (next < source.Length && (source[next] == '}' || source[next] == ']')) continue;
            }
            clean.Append(c);
        }
        try { return new JavaScriptSerializer { MaxJsonLength = int.MaxValue }.Deserialize<Dictionary<string, object>>(clean.ToString()); }
        catch (Exception ex) { throw new InvalidDataException("Cannot read " + path + ": " + ex.Message); }
    }

    static int Port(Dictionary<string, object> values, string key)
    {
        object value;
        int port;
        if (!values.TryGetValue(key, out value) || !int.TryParse(Convert.ToString(value), out port) || port < 1 || port > 65535)
            throw new InvalidDataException("Invalid " + key + " in settings.");
        return port;
    }

    /// <summary>Checks paths and ports; returns the two ports. Throws with a plain message on any problem.</summary>
    public static int[] Validate(string root)
    {
        var server = ReadLoose(Path.Combine(root, "Data", "Settings.json"));
        var client = ReadLoose(Path.Combine(root, "Data", "ClientData", "ClientSettings.json"));
        int port = Port(server, "BasePort"), session = Port(server, "SessionServerPort");
        if (port == session) throw new InvalidDataException("BasePort and SessionServerPort must differ.");
        if (Port(client, "BasePort") != port || Port(client, "SessionServerPort") != session)
            throw new InvalidDataException("Client and server ports differ. Match them in Data\\Settings.json and Data\\ClientData\\ClientSettings.json.");
        foreach (string file in new[] { "YgoMaster.exe", "YgoMasterClient.exe", "YgoMasterLoader.dll", Path.Combine("Data", "BalancedCharacters", "Mode.json") })
            if (!File.Exists(Path.Combine(root, file))) throw new FileNotFoundException("Missing game file: " + file + ". Reinstall the mod.");
        string game = Path.GetDirectoryName(Path.GetFullPath(root).TrimEnd('\\'));
        if (!File.Exists(Path.Combine(game, "masterduel.exe"))) throw new FileNotFoundException("This folder must be inside the Master Duel folder, next to masterduel.exe.");
        if (!Directory.Exists(Path.Combine(game, "LocalData"))) throw new DirectoryNotFoundException("Master Duel's downloaded data (LocalData) is missing. Start Master Duel once from Steam.");
        return new[] { port, session };
    }

    static HashSet<int> ListeningPorts()
    {
        return new HashSet<int>(System.Net.NetworkInformation.IPGlobalProperties.GetIPGlobalProperties().GetActiveTcpListeners().Select(x => x.Port));
    }

    static List<Process> OwnServers(string serverPath)
    {
        var result = new List<Process>();
        foreach (var process in Process.GetProcessesByName("YgoMaster"))
        {
            try { if (string.Equals(process.MainModule.FileName, serverPath, StringComparison.OrdinalIgnoreCase)) result.Add(process); }
            catch { }
        }
        return result;
    }

    /// <summary>
    /// For every deck set in Mode.json "sets": installs its texts as ClientData/IDS/IDS_BALANCED_&lt;REVISION&gt;.txt
    /// (the client loads every file in that folder) and merges the gate thumbnails into
    /// BalancedCharacters/Generated/SoloGateCards.txt. Returns the number of sets.
    /// </summary>
    public static int PrepareSets(string root)
    {
        string modeRoot = Path.Combine(root, "Data", "BalancedCharacters");
        var mode = ReadLoose(Path.Combine(modeRoot, "Mode.json"));
        object raw;
        if (!mode.TryGetValue("sets", out raw) || !(raw is IList)) return 0;
        string idsDir = Path.Combine(root, "Data", "ClientData", "IDS");
        var thumbs = new List<string>();
        int count = 0;
        foreach (var entry in ((IList)raw).OfType<Dictionary<string, object>>())
        {
            string revision = entry.ContainsKey("revision") ? entry["revision"] as string : null;
            if (string.IsNullOrEmpty(revision) || revision.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0) continue;
            string pack = Path.Combine(modeRoot, "Revisions", revision);
            string text = Path.Combine(pack, "IDS_BALANCED_CHARACTERS.txt"), cards = Path.Combine(pack, "SoloGateCards.txt");
            if (!File.Exists(text) || !File.Exists(cards)) throw new FileNotFoundException("Deck set " + revision + " is incomplete. Reinstall the mod.");
            string target = Path.Combine(idsDir, "IDS_BALANCED_" + revision.ToUpperInvariant().Replace('-', '_') + ".txt");
            string content = File.ReadAllText(text);
            if (!File.Exists(target) || File.ReadAllText(target) != content) File.WriteAllText(target, content, new UTF8Encoding(false));
            thumbs.AddRange(File.ReadAllLines(cards).Where(x => x.Trim().Length > 0));
            count++;
        }
        // The single-set text file holds the same texts as one of the sets; keep one copy only.
        string single = Path.Combine(idsDir, "IDS_BALANCED_CHARACTERS.txt");
        if (count > 0 && File.Exists(single)) File.Delete(single);
        string merged = Path.Combine(modeRoot, "Generated", "SoloGateCards.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(merged));
        string mergedText = string.Join("\n", thumbs) + "\n";
        if (!File.Exists(merged) || File.ReadAllText(merged) != mergedText) File.WriteAllText(merged, mergedText, new UTF8Encoding(false));
        return count;
    }

    public enum NetMode { Offline, Host, Join }

    /// <summary>
    /// Switches Data/Settings.json and Data/ClientData/ClientSettings.json between playing alone (Offline),
    /// hosting for other players (Host, server open on the network) and playing on another PC's server (Join).
    /// Values follow Docs/PvP.md. Files are only rewritten when something changes.
    /// </summary>
    public static void ApplyNetwork(string root, NetMode mode, string address)
    {
        string serverPath = Path.Combine(root, "Data", "Settings.json");
        string clientPath = Path.Combine(root, "Data", "ClientData", "ClientSettings.json");
        var server = ReadLoose(serverPath);
        var client = ReadLoose(clientPath);
        bool serverChanged = false, clientChanged = false;
        Action<Dictionary<string, object>, string, object, bool> set = (values, key, value, isServer) =>
        {
            object old;
            if (values.TryGetValue(key, out old) && Equals(Convert.ToString(old), Convert.ToString(value))) return;
            values[key] = value;
            if (isServer) serverChanged = true; else clientChanged = true;
        };
        if (mode == NetMode.Offline)
        {
            set(server, "MultiplayerEnabled", false, true);
            set(server, "BaseIP", "localhost", true);
            set(server, "BindIP", "http://{BaseIP}:{BasePort}/", true);
            set(server, "SessionServerIP", "{BaseIP}", true);
            set(server, "MultiplayerPvpClientConnectIP", "{SessionServerIP}", true);
            set(client, "BaseIP", "localhost", false);
        }
        else
        {
            if (string.IsNullOrWhiteSpace(address)) throw new ArgumentException("Enter the server address.");
            address = address.Trim();
            if (mode == NetMode.Host)
            {
                set(server, "MultiplayerEnabled", true, true);
                set(server, "BaseIP", address, true);
                set(server, "BindIP", "http://*:{BasePort}/", true);
                set(server, "SessionServerIP", "0.0.0.0", true);
                set(server, "MultiplayerPvpClientConnectIP", "localhost", true);
            }
            set(client, "BaseIP", address, false);
            // Every player needs their own token, otherwise two players share one account on the server.
            object token;
            if (!client.TryGetValue("MultiplayerToken", out token) || string.IsNullOrWhiteSpace(Convert.ToString(token)))
                set(client, "MultiplayerToken", "player-" + Guid.NewGuid().ToString("N").Substring(0, 12), false);
        }
        var json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
        if (serverChanged) File.WriteAllText(serverPath, json.Serialize(server), new UTF8Encoding(false));
        if (clientChanged) File.WriteAllText(clientPath, json.Serialize(client), new UTF8Encoding(false));
    }

    /// <summary>The address saved for joining (the client's BaseIP), or "" when it is still local.</summary>
    public static string SavedServerAddress(string root)
    {
        var client = ReadLoose(Path.Combine(root, "Data", "ClientData", "ClientSettings.json"));
        object value;
        string address = client.TryGetValue("BaseIP", out value) ? Convert.ToString(value) : "";
        return address == "localhost" || address == "127.0.0.1" ? "" : address;
    }

    /// <summary>This PC's network addresses, private-network apps (Tailscale 100.x, Radmin 26.x) first.</summary>
    public static List<string> LocalAddresses()
    {
        var result = new List<string>();
        foreach (var nic in System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces())
        {
            if (nic.OperationalStatus != System.Net.NetworkInformation.OperationalStatus.Up) continue;
            foreach (var unicast in nic.GetIPProperties().UnicastAddresses)
            {
                var ip = unicast.Address;
                if (ip.AddressFamily != System.Net.Sockets.AddressFamily.InterNetwork || System.Net.IPAddress.IsLoopback(ip)) continue;
                string text = ip.ToString();
                if (text.StartsWith("169.254.")) continue;
                if (!result.Contains(text)) result.Add(text);
            }
        }
        Func<string, int> rank = a => a.StartsWith("100.") ? 0 : a.StartsWith("26.") || a.StartsWith("25.") ? 1
            : a.StartsWith("192.168.") || a.StartsWith("10.") || a.StartsWith("172.") ? 2 : 3;
        return result.OrderBy(rank).ToList();
    }

    public static bool IsAdministrator()
    {
        try { return new System.Security.Principal.WindowsPrincipal(System.Security.Principal.WindowsIdentity.GetCurrent()).IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator); }
        catch { return false; }
    }

    static bool CanReach(string address, int port)
    {
        try
        {
            using (var tcp = new System.Net.Sockets.TcpClient())
            {
                var attempt = tcp.BeginConnect(address, port, null, null);
                bool done = attempt.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(4));
                if (done) tcp.EndConnect(attempt);
                return done && tcp.Connected;
            }
        }
        catch { return false; }
    }

    /// <summary>Join mode: starts only Master Duel, connected to another PC's server (no local server).</summary>
    public static string StartClientOnly(string root, string address, Action<string> progress)
    {
        int[] ports = Validate(root);
        PrepareSets(root);
        progress("Checking the server at " + address + "...");
        if (!CanReach(address, ports[0]))
            throw new InvalidOperationException("Can't reach the server at " + address + " (port " + ports[0] + "). Check that the host has pressed Host a server, " +
                "that you are both in the same private network app (Tailscale, ZeroTier, Radmin), and that the address is right.");
        progress("Starting Master Duel...");
        Process.Start(new ProcessStartInfo(Path.Combine(root, "YgoMasterClient.exe")) { WorkingDirectory = root, UseShellExecute = true, WindowStyle = ProcessWindowStyle.Hidden });
        try { HideSupportFiles(root); } catch { }
        return "Master Duel is starting, connected to " + address + ".";
    }

    public static string Start(string root, Action<string> progress)
    {
        int[] ports = Validate(root);
        PrepareSets(root);
        string serverPath = Path.GetFullPath(Path.Combine(root, "YgoMaster.exe"));
        // Restart only this folder's own server so saved settings load; other mod servers are left alone.
        foreach (var process in OwnServers(serverPath))
        {
            process.Kill();
            if (!process.WaitForExit(5000)) throw new InvalidOperationException("The old server did not stop.");
        }
        var busy = ListeningPorts();
        if (busy.Contains(ports[0]) || busy.Contains(ports[1]))
            throw new InvalidOperationException("Port " + ports[0] + " or " + ports[1] + " is used by another program. Close it or change the ports in the settings files.");
        string logs = Path.Combine(root, "LaunchLogs");
        Directory.CreateDirectory(logs);
        string stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss-fff");
        // Through cmd so the server keeps writing its logs after this window closes.
        string cmd = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "cmd.exe");
        string line = "/c \"\"" + serverPath + "\" > \"" + Path.Combine(logs, stamp + "-server.log") + "\" 2> \"" + Path.Combine(logs, stamp + "-server-error.log") + "\"\"";
        var host = Process.Start(new ProcessStartInfo(cmd, line) { WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true });
        progress("Waiting for the server...");
        bool ready = false;
        for (int i = 0; i < 300 && !ready; i++)
        {
            if (host.HasExited) throw new InvalidOperationException("The server stopped while starting.");
            var open = ListeningPorts();
            ready = open.Contains(ports[0]) && open.Contains(ports[1]);
            if (!ready) System.Threading.Thread.Sleep(100);
        }
        if (!ready)
        {
            bool open = ReadLoose(Path.Combine(root, "Data", "Settings.json")).ContainsKey("BindIP") &&
                Convert.ToString(ReadLoose(Path.Combine(root, "Data", "Settings.json"))["BindIP"]).Contains("*");
            throw new TimeoutException("The server did not open ports " + ports[0] + " / " + ports[1] + " within 30 seconds." +
                (open && !IsAdministrator() ? " Hosting for other players needs administrator rights: use Host a server and confirm the Windows prompt, or press Start Game to play alone." : ""));
        }
        progress("Starting Master Duel...");
        Process.Start(new ProcessStartInfo(Path.Combine(root, "YgoMasterClient.exe")) { WorkingDirectory = root, UseShellExecute = true, WindowStyle = ProcessWindowStyle.Hidden });
        try { HideSupportFiles(root); } catch { }
        return "Master Duel is starting.";
    }

    public static void LogError(string root, string message)
    {
        try
        {
            string logs = Path.Combine(root, "LaunchLogs");
            Directory.CreateDirectory(logs);
            File.AppendAllText(Path.Combine(logs, "Launcher-errors.log"), DateTime.Now.ToString("s") + " " + message + Environment.NewLine);
        }
        catch { }
    }
}

static class Program
{
    [STAThread] static int Main(string[] args)
    {
        try
        {
            string root = args.Length > 1 ? args[1] : AppDomain.CurrentDomain.BaseDirectory;
            if (args.Length > 0 && args[0] == "--check") { EditorDocument.CheckRuntime(root); Console.WriteLine("PASS balanced editor loads installed settings and required files"); return 0; }
            if (args.Length > 0 && args[0] == "--validate")
            {
                // "Start Game.exe" --validate [runtime folder]: launch checks without starting anything (was Start-Balanced.ps1 -ValidateOnly)
                int[] ports = GameLauncher.Validate(root);
                Console.WriteLine("PASS balanced launch paths and matching configured ports: " + ports[0] + " / " + ports[1]);
                return 0;
            }
            if (args.Length > 0 && args[0] == "--hide") { GameLauncher.HideSupportFiles(root); Console.WriteLine("Support files hidden in " + root); return 0; }
            if (args.Length > 0 && args[0] == "--prepare-sets") { Console.WriteLine("Prepared " + GameLauncher.PrepareSets(root) + " deck sets in " + root); return 0; }
            if (args.Length > 0 && args[0] == "--self-test") { EditorDocument.SelfTest(root); return 0; }
            if (args.Length > 1 && args[0] == "--deck-set")
            {
                // "Start Game.exe" --deck-set <revision> [runtime folder]
                root = args.Length > 2 ? args[2] : AppDomain.CurrentDomain.BaseDirectory;
                var doc = new EditorDocument(root);
                doc.SelectedRevision = args[1];
                doc.Save();
                Console.WriteLine("Deck set is now " + doc.CurrentRevision + " (takes effect when the balanced server starts)");
                return 0;
            }
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
            if (args.Length > 1 && args[0] == "--screenshot")
            {
                // "Start Game.exe" --screenshot <out.png> [runtime folder]: render the window to an image
                root = args.Length > 2 ? args[2] : AppDomain.CurrentDomain.BaseDirectory;
                using (var form = new BalancedEditorForm(root))
                {
                    var timer = new Timer { Interval = 500 };
                    form.Shown += (s, e) => timer.Start();
                    timer.Tick += (s, e) => {
                        timer.Stop();
                        using (var bmp = new Bitmap(form.Width, form.Height)) { form.DrawToBitmap(bmp, new Rectangle(0, 0, form.Width, form.Height)); bmp.Save(args[1]); }
                        form.Close(); };
                    Application.Run(form); timer.Dispose();
                }
                Console.WriteLine("Saved " + args[1]);
                return 0;
            }
            if (args.Length > 1 && args[0] == "--net")
            {
                // "Start Game.exe" --net offline|host <address>|join <address> [runtime folder]: apply a network mode only (tests)
                var mode = (GameLauncher.NetMode)Enum.Parse(typeof(GameLauncher.NetMode), args[1], true);
                string address = mode == GameLauncher.NetMode.Offline ? null : args[2];
                root = args.Length > (mode == GameLauncher.NetMode.Offline ? 2 : 3) ? args[mode == GameLauncher.NetMode.Offline ? 2 : 3] : AppDomain.CurrentDomain.BaseDirectory;
                GameLauncher.ApplyNetwork(root, mode, address);
                Console.WriteLine("Network mode " + mode + (address != null ? " " + address : "") + " applied in " + root);
                return 0;
            }
            if (args.Length > 1 && args[0] == "--host")
            {
                // Restarted as administrator by Host a server: host on the chosen address straight away.
                root = args.Length > 2 ? args[2] : AppDomain.CurrentDomain.BaseDirectory;
                using (var hostForm = new BalancedEditorForm(root))
                {
                    string address = args[1];
                    hostForm.Shown += (s, e) => { try { hostForm.Launch(GameLauncher.NetMode.Host, address); } catch (Exception error) { MessageBox.Show(hostForm, error.Message, "Host a server", MessageBoxButtons.OK, MessageBoxIcon.Error); } };
                    Application.Run(hostForm);
                }
                return 0;
            }
            using (var form = new BalancedEditorForm(root))
            {
                if (args.Length > 0 && args[0] == "--smoke-test")
                {
                    var timer = new Timer { Interval = 350 };
                    bool shown = false;
                    form.Shown += (s, e) => { shown = true; timer.Start(); };
                    timer.Tick += (s, e) => { timer.Stop(); form.Close(); };
                    Application.Run(form); timer.Dispose();
                    if (!shown) throw new Exception("Editor window did not reach Shown.");
                    Console.WriteLine("PASS real WinForms window created, shown and closed without saving");
                }
                else Application.Run(form);
            }
            return 0;
        }
        catch (Exception ex)
        {
            if (args.Length > 0 && args[0].StartsWith("--")) Console.Error.WriteLine(ex.ToString());
            else MessageBox.Show(ex.Message, "Balanced settings editor", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
