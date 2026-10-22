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

public sealed class EditorDocument
{
    public readonly string Root, SettingsPath, ModePath;
    public readonly GeneralSettings Values = new GeneralSettings();
    public bool Enabled;
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
        string newSettings = Json.Serialize(settings), newMode = Json.Serialize(mode);
        string stamp = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6);
        string settingsBackup = SettingsPath + ".before-balanced-editor-" + stamp + ".bak";
        string modeBackup = ModePath + ".before-balanced-editor-" + stamp + ".bak";
        Read(newSettings); Read(newMode);
        File.Copy(SettingsPath, settingsBackup);
        File.Copy(ModePath, modeBackup);
        try
        {
            File.WriteAllText(SettingsPath, newSettings, new UTF8Encoding(false));
            File.WriteAllText(ModePath, newMode, new UTF8Encoding(false));
            if (File.ReadAllText(SettingsPath) != newSettings || File.ReadAllText(ModePath) != newMode)
                throw new IOException("Saved settings did not match the requested values.");
            originalSettings = newSettings; originalMode = newMode;
        }
        catch (Exception saveError)
        {
            try
            {
                File.WriteAllText(SettingsPath, originalSettings, new UTF8Encoding(false));
                File.WriteAllText(ModePath, originalMode, new UTF8Encoding(false));
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

public sealed class BalancedEditorForm : Form
{
    readonly EditorDocument document;
    readonly CheckBox enabled;
    readonly Label status;
    readonly PropertyGrid grid;
    public BalancedEditorForm(string root)
    {
        document = new EditorDocument(root);
        Text = "Balanced Characters - Settings Editor";
        StartPosition = FormStartPosition.CenterScreen; Size = new Size(820, 700); MinimumSize = new Size(700, 600);
        Font = new Font("Segoe UI", 10);
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, RowCount = 6, ColumnCount = 1, Padding = new Padding(16) };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 55));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 38));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 65));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 45));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 35));
        Controls.Add(layout);
        var path = new TextBox { Text = document.Root, ReadOnly = true, Multiline = true, Dock = DockStyle.Fill };
        layout.Controls.Add(path, 0, 0);
        enabled = new CheckBox { Text = "Enable Balanced Character Duels (Kaiba / Joey prototype)", Checked = document.Enabled, Dock = DockStyle.Fill };
        layout.Controls.Add(enabled, 0, 1);
        grid = new PropertyGrid { SelectedObject = document.Values, Dock = DockStyle.Fill, ToolbarVisible = false, HelpVisible = true };
        layout.Controls.Add(grid, 0, 2);
        layout.Controls.Add(new Label { Text = "Balanced encounters keep fixed decks, 8000 LP and their CPU rules. Standard campaign reward settings do not add rewards to balanced free duels. Saved changes require a server restart.", Dock = DockStyle.Fill }, 0, 3);
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
        AddButton(buttons, "Save", () => Save());
        AddButton(buttons, "Save and start balanced", () => { if (Process.GetProcessesByName("masterduel").Length > 0) throw new InvalidOperationException("Close Master Duel before restarting the balanced server."); Save(); StartBalanced(); });
        AddButton(buttons, "Open original editor", () => { Process.Start(new ProcessStartInfo(Path.Combine(document.Root, "SettingsEditor.exe")) { WorkingDirectory = document.Root, UseShellExecute = true }); status.Text = "Close and reopen this editor after saving in the original editor."; });
        AddButton(buttons, "Close", () => Close());
        layout.Controls.Add(buttons, 0, 4);
        status = new Label { Text = "Loaded. No settings changed.", Dock = DockStyle.Fill };
        layout.Controls.Add(status, 0, 5);
    }
    void AddButton(FlowLayoutPanel panel, string text, Action action)
    {
        var button = new Button { Text = text, AutoSize = true, Height = 33 };
        button.Click += (s, e) => { try { action(); } catch (Exception ex) { status.Text = ex.Message; MessageBox.Show(this, ex.Message, "Balanced settings", MessageBoxButtons.OK, MessageBoxIcon.Error); } };
        panel.Controls.Add(button);
    }
    void Save() { ValidateChildren(); document.Enabled = enabled.Checked; document.Save(); status.Text = "Saved with backups. Other settings and saves preserved."; }
    void StartBalanced()
    {
        string launcher = Path.Combine(document.Root, "Start-Balanced.ps1");
        if (!File.Exists(launcher)) throw new FileNotFoundException("Start-Balanced.ps1 is missing. Install the full editor package.");
        Process.Start(new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File \"" + launcher + "\"") { WorkingDirectory = document.Root, UseShellExecute = false, CreateNoWindow = true });
        status.Text = "Starting balanced server and client. Check LaunchLogs if startup fails.";
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
            if (args.Length > 0 && args[0] == "--self-test") { EditorDocument.SelfTest(root); return 0; }
            Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
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
