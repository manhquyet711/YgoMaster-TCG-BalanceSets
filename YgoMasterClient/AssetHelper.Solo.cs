using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using IL2CPP;
using System.IO;

namespace YgoMasterClient
{
    unsafe static partial class AssetHelper
    {
        static Dictionary<int, SoloGateCardEntry> SoloGates = new Dictionary<int, SoloGateCardEntry>();
        static Dictionary<int, string> SoloGateBackgroundPaths = new Dictionary<int, string>();

        // YgomGame.Solo.SoloCardThumbSettings
        static IL2Class soloCardThumbSettingsClassInfo;
        static IL2Field fieldGateMap;
        static IL2Field fieldChapterMap;

        // Newer clients may already have cached SettingMap lookups when the
        // resource hook appends custom gates to m_Settings. Apply the configured
        // gate thumbnail at the lookup boundary as well, before card art loads.
        delegate IntPtr Del_GetSoloThumbSetting(IntPtr thisPtr, int format, int id);
        static Hook<Del_GetSoloThumbSetting> hookGetSoloThumbSetting;
        delegate csbool Del_HasSoloThumbSetting(IntPtr thisPtr, int format, int id);
        static Hook<Del_HasSoloThumbSetting> hookHasSoloThumbSetting;
        static HashSet<int> loggedSoloThumbRepairs = new HashSet<int>();
        const int SoloThumbFormatGate = 0;
        static int soloLookupLogCount;
        static int soloZeroRequestLogCount;
        static HashSet<int> balancedSoloChapterIds = new HashSet<int>();

        internal static bool IsBalancedSoloChapter(int chapterId)
        {
            return balancedSoloChapterIds.Contains(chapterId);
        }

        internal static int[] BalancedSoloChapterIdsForGate(int gateId)
        {
            return balancedSoloChapterIds.Where(id => id / 10000 == gateId).ToArray();
        }

        internal static void LogBalancedSoloUi(string message)
        {
            LogSoloThumbnail("[chapter-map-0.2.1] " + message);
        }

        static void LogSoloThumbnail(string message)
        {
            try
            {
                File.AppendAllText(Path.Combine(Program.CurrentDir, "SoloThumbnailFix.log"),
                    DateTime.UtcNow.ToString("o") + " [startup-v3] " + message + Environment.NewLine);
            }
            catch { }
        }

        static void TraceSoloImageRequest(IntPtr path)
        {
            if (path == IntPtr.Zero) return;
            string value = new IL2String(path).ToString();
            if (value != null && value.IndexOf("Card/Images/Illust/0000", StringComparison.OrdinalIgnoreCase) >= 0 &&
                System.Threading.Interlocked.Increment(ref soloZeroRequestLogCount) <= 3)
                LogSoloThumbnail("ZERO CARD REQUEST " + value + "\n" + Environment.StackTrace);
        }

        // YgomGame.Solo.SoloCardThumbSettings.SettingMap
        static IL2Class settingMapClassInfo;
        static IL2Field fieldThumbMapSettings;
        static IL2Field fieldThumbMapSettingsMap;

        // YgomGame.Solo.SoloCardThumbSettings.ThumbSetting
        static IL2Class thumbSettingClassInfo;
        static IL2Method thumbSettingCtor;
        static IL2Field fieldThumbSettingId;
        static IL2Field fieldThumbSettingMrk;
        static IL2Field fieldThumbSettingUvRectPos;
        static IL2Field fieldThumbSettingUvRectSize;
        static IL2Field fieldThumbSettingUvRectPosOther;
        static IL2Field fieldThumbSettingUvRectSizeOther;

        // The thumb data only gets loaded once, store the pointer so that we can reload our custom data as needed
        static IntPtr soloThumbsPtr;

        /// <summary>
        /// YgomGame.Solo.SoloCardThumbSettings.ThumbSetting
        /// </summary>
        class SoloGateCardEntry
        {
            public int Id;
            public int CardId;
            public Vector2 UvRectPos;
            public Vector2 UvRectSize;
            public Vector2 UvRectPosOther;
            public Vector2 UvRectSizeOther;
        }

        static void InitSoloTypes()
        {
            LogSoloThumbnail("Initializing thumbnail types");
            IL2Assembly assembly = Assembler.GetAssembly("Assembly-CSharp");
            soloCardThumbSettingsClassInfo = assembly.GetClass("SoloCardThumbSettings");
            fieldGateMap = soloCardThumbSettingsClassInfo.GetField("m_GateMap");
            fieldChapterMap = soloCardThumbSettingsClassInfo.GetField("m_ChapterMap");
            settingMapClassInfo = soloCardThumbSettingsClassInfo.GetNestedType("SettingMap");
            fieldThumbMapSettings = settingMapClassInfo.GetField("m_Settings");
            fieldThumbMapSettingsMap = settingMapClassInfo.GetField("m_SettingsMap");
            thumbSettingClassInfo = soloCardThumbSettingsClassInfo.GetNestedType("ThumbSetting");
            thumbSettingCtor = thumbSettingClassInfo.GetMethod(".ctor");
            fieldThumbSettingId = thumbSettingClassInfo.GetField("id");
            fieldThumbSettingMrk = thumbSettingClassInfo.GetField("mrk");
            fieldThumbSettingUvRectPos = thumbSettingClassInfo.GetField("uvRectPos");
            fieldThumbSettingUvRectSize = thumbSettingClassInfo.GetField("uvRectSize");
            fieldThumbSettingUvRectPosOther = thumbSettingClassInfo.GetField("uvRectPosOther");
            fieldThumbSettingUvRectSizeOther = thumbSettingClassInfo.GetField("uvRectSizeOther");

            IL2Method getSetting = soloCardThumbSettingsClassInfo.GetMethod("GetSetting",
                x => x.GetParameters().Length == 2);
            IL2Method hasSetting = soloCardThumbSettingsClassInfo.GetMethod("IsExitsSetting",
                x => x.GetParameters().Length == 2);
            if (getSetting == null || hasSetting == null)
            {
                throw new InvalidOperationException("Solo thumbnail lookup signatures are incompatible with this game version.");
            }
            hookGetSoloThumbSetting = new Hook<Del_GetSoloThumbSetting>(GetSoloThumbSetting, getSetting);
            hookHasSoloThumbSetting = new Hook<Del_HasSoloThumbSetting>(HasSoloThumbSetting, hasSetting);
            LogSoloThumbnail("Initialized root lookup hooks; client=" + typeof(AssetHelper).Assembly.Location);
        }

        static csbool HasSoloThumbSetting(IntPtr thisPtr, int format, int id)
        {
            SoloGateCardEntry entry;
            if (format == SoloThumbFormatGate && SoloGates.TryGetValue(id, out entry) && entry.CardId > 0)
            {
                return true;
            }
            return hookHasSoloThumbSetting.Original(thisPtr, format, id);
        }

        static IntPtr GetSoloThumbSetting(IntPtr thisPtr, int format, int id)
        {
            IntPtr setting = hookGetSoloThumbSetting.Original(thisPtr, format, id);
            if (System.Threading.Interlocked.Increment(ref soloLookupLogCount) <= 40)
                LogSoloThumbnail("Lookup format=" + format + " id=" + id + " card=" +
                    (setting == IntPtr.Zero ? "null" : fieldThumbSettingMrk.GetValue(setting).GetValueRef<int>().ToString()));
            SoloGateCardEntry entry;
            if (format == SoloThumbFormatGate && setting != IntPtr.Zero &&
                SoloGates.TryGetValue(id, out entry) && entry.CardId > 0)
            {
                int previousCard = fieldThumbSettingMrk.GetValue(setting).GetValueRef<int>();
                // Only touch gate thumbnails explicitly declared in SoloGateCards.txt.
                // Chapter, loot-source and standard gate settings are left alone.
                InjectSoloThumb(setting, entry);
                if (loggedSoloThumbRepairs.Add(id))
                {
                    string message = "[SoloThumbnailFix] gate=" + id + " oldCard=" + previousCard +
                        " configuredCard=" + entry.CardId;
                    Console.WriteLine(message);
                    try
                    {
                        File.AppendAllText(Path.Combine(Program.CurrentDir, "SoloThumbnailFix.log"),
                            DateTime.UtcNow.ToString("o") + " " + message + Environment.NewLine);
                    }
                    catch { }
                }
            }
            return setting;
        }

        public static void LoadSoloData()
        {
            LogSoloThumbnail("Loading data=" + Program.DataDir + " clientData=" + Program.ClientDataDir);
            SoloGates.Clear();
            SoloGateBackgroundPaths.Clear();
            balancedSoloChapterIds.Clear();
            try
            {
                string modeRoot = Path.Combine(Program.DataDir, "BalancedCharacters");
                string modePath = Path.Combine(modeRoot, "Mode.json");
                string overlayPath = Path.Combine(modeRoot, "Generated", "Overlay.json");
                if (File.Exists(modePath) && File.Exists(overlayPath))
                {
                    var mode = MiniJSON.Json.DeserializeStripped(File.ReadAllText(modePath)) as Dictionary<string, object>;
                    if (mode != null && YgoMaster.Utils.GetValue<bool>(mode, "enabled"))
                    {
                        var overlay = MiniJSON.Json.DeserializeStripped(File.ReadAllText(overlayPath)) as Dictionary<string, object>;
                        var chapters = YgoMaster.Utils.GetDictionary(overlay, "chapter");
                        if (chapters != null)
                            foreach (var gate in chapters.Values)
                            {
                                var entries = gate as Dictionary<string, object>;
                                if (entries == null) continue;
                                foreach (string key in entries.Keys)
                                {
                                    int chapterId;
                                    if (int.TryParse(key, out chapterId) && chapterId > 0)
                                        balancedSoloChapterIds.Add(chapterId);
                                }
                            }
                    }
                }
                LogBalancedSoloUi("Configured chapters=" + string.Join(",", balancedSoloChapterIds));
            }
            catch (Exception error)
            {
                balancedSoloChapterIds.Clear();
                LogBalancedSoloUi("Chapter configuration unavailable: " + error.Message);
            }

            string backgroundsDir = Path.Combine(Program.ClientDataDir, "SoloGateBackgrounds");
            if (Directory.Exists(backgroundsDir))
            {
                foreach (string backgroundFile in Directory.GetFiles(backgroundsDir))
                {
                    int id;
                    if (int.TryParse(Path.GetFileNameWithoutExtension(backgroundFile), out id))
                    {
                        SoloGateBackgroundPaths[id] = backgroundFile;
                    }
                }
            }

            foreach (string file in new string[] {
                Path.Combine(Program.ClientDataDir, "SoloGateCards.txt"),
                Path.Combine(Program.DataDir, "BalancedCharacters", "Generated", "SoloGateCards.txt") })
            {
                if (!File.Exists(file))
                {
                    LogSoloThumbnail("Optional thumbnail file missing: " + file);
                    continue;
                }
                LogSoloThumbnail("Reading thumbnail file: " + file);
                char[] splitChars = { ',', '|' };
                string[] lines = File.ReadAllLines(file);
                foreach (string line in lines)
                {
                    if (string.IsNullOrWhiteSpace(line))
                    {
                        continue;
                    }
                    string[] splitted = line.Split(splitChars, StringSplitOptions.RemoveEmptyEntries);
                    if (splitted.Length == 0 || splitted[0].Trim().StartsWith("//"))
                    {
                        continue;
                    }
                    if (splitted.Length >= 4)
                    {
                        SoloGateCardEntry entry = new SoloGateCardEntry();
                        if (int.TryParse(splitted[0], out entry.Id) &&
                            int.TryParse(splitted[1], out entry.CardId))
                        {
                            if (splitted.Length >= 10)
                            {
                                if (float.TryParse(splitted[2], out entry.UvRectPos.x) &&
                                    float.TryParse(splitted[3], out entry.UvRectPos.y) &&
                                    float.TryParse(splitted[4], out entry.UvRectSize.x) &&
                                    float.TryParse(splitted[5], out entry.UvRectSize.y) &&
                                    float.TryParse(splitted[6], out entry.UvRectPosOther.x) &&
                                    float.TryParse(splitted[7], out entry.UvRectPosOther.y) &&
                                    float.TryParse(splitted[8], out entry.UvRectSizeOther.x) &&
                                    float.TryParse(splitted[9], out entry.UvRectSizeOther.y))
                                {
                                    SoloGates[entry.Id] = entry;
                                }
                            }
                            else
                            {
                                if (float.TryParse(splitted[2], out entry.UvRectPos.y) &&
                                    float.TryParse(splitted[3], out entry.UvRectPosOther.y))
                                {
                                    entry.UvRectPos.x = 0;
                                    entry.UvRectPosOther.x = 0;
                                    entry.UvRectSize = new Vector2(1, 1);
                                    entry.UvRectSizeOther = new Vector2(1, 1);
                                    SoloGates[entry.Id] = entry;
                                }
                            }
                        }
                    }
                }
            }
            LogSoloThumbnail("Configured gates=" + string.Join(",", SoloGates.Keys));
            if (soloThumbsPtr != IntPtr.Zero)
            {
                InjectSoloThumbs(soloThumbsPtr);
            }
        }

        static void InjectSoloThumb(IntPtr thumb, SoloGateCardEntry data)
        {
            int mrk = data.CardId;
            Vector2 rectPos = data.UvRectPos;
            Vector2 rectSize = data.UvRectSize;
            Vector2 rectPosOther = data.UvRectPosOther;
            Vector2 rectSizeOther = data.UvRectSizeOther;
            fieldThumbSettingMrk.SetValue(thumb, new IntPtr(&mrk));
            fieldThumbSettingUvRectPos.SetValue(thumb, new IntPtr(&rectPos));
            fieldThumbSettingUvRectSize.SetValue(thumb, new IntPtr(&rectSize));
            fieldThumbSettingUvRectPosOther.SetValue(thumb, new IntPtr(&rectPosOther));
            fieldThumbSettingUvRectSizeOther.SetValue(thumb, new IntPtr(&rectSizeOther));
        }

        static void InjectSoloThumbs(IntPtr obj)
        {
            soloThumbsPtr = obj;
            LogSoloThumbnail("Resource received; injecting gate thumbnails");
            // NOTE: Not modifying m_ChapterMap as those card images are only used for scenario chapters

            // NOTE: When loading the m_SettingsMap seems to be empty. It's probably filled in later on
            IL2Object gateMapObj = fieldGateMap.GetValue(obj);
            if (gateMapObj != null)
            {
                IL2Object settingsObj = fieldThumbMapSettings.GetValue(gateMapObj.ptr);
                IL2Object settingsMapObj = fieldThumbMapSettingsMap.GetValue(gateMapObj.ptr);
                if (settingsObj != null)
                {
                    StringBuilder dataDump = null;
                    IL2ListExplicit settingsList = new IL2ListExplicit(settingsObj.ptr, thumbSettingClassInfo);
                    // Resolve the actual closed Dictionary<int, ThumbSetting> type.
                    // The shared generic wrapper's type cache is unsuitable here.
                    IL2Method cacheSetter = null;
                    if (settingsMapObj != null)
                    {
                        IL2Class cacheClass = new IL2Class(Import.Object.il2cpp_object_get_class(settingsMapObj.ptr));
                        int cacheCount = cacheClass.GetProperty("Count").GetGetMethod()
                            .Invoke(settingsMapObj.ptr).GetValueRef<int>();
                        // Leave an empty cache empty: native lazy initialization must
                        // still register every standard gate from the complete list.
                        if (cacheCount > 0) cacheSetter = cacheClass.GetProperty("Item").GetSetMethod();
                        LogSoloThumbnail("Existing cache entries=" + cacheCount);
                    }
                    HashSet<int> seenIds = new HashSet<int>();
                    for (int j = 0; j < settingsList.Count; j++)
                    {
                        IntPtr setting = settingsList[j];
                        int id = fieldThumbSettingId.GetValue(setting).GetValueRef<int>();
                        seenIds.Add(id);
                        SoloGateCardEntry customSetting;
                        if (SoloGates.TryGetValue(id, out customSetting))
                        {
                            InjectSoloThumb(setting, customSetting);
                            if (cacheSetter != null)
                                cacheSetter.Invoke(settingsMapObj.ptr, new IntPtr[] { new IntPtr(&id), setting });
                            LogSoloThumbnail("Updated gate=" + id + " card=" + customSetting.CardId + " cache=" + (cacheSetter != null));
                        }
                        if (ClientSettings.AssetHelperDump)
                        {
                            if (dataDump == null)
                            {
                                dataDump = new StringBuilder();
                            }
                            int mrk = fieldThumbSettingMrk.GetValue(setting).GetValueRef<int>();
                            Vector2 rectPos = fieldThumbSettingUvRectPos.GetValue(setting).GetValueRef<Vector2>();
                            //Vector2 rectSize = fieldThumbSettingUvRectSize.GetValue(setting).GetValueRef<Vector2>();
                            Vector2 rectPosOther = fieldThumbSettingUvRectPosOther.GetValue(setting).GetValueRef<Vector2>();
                            //Vector2 rectSizeOther = fieldThumbSettingUvRectSizeOther.GetValue(setting).GetValueRef<Vector2>();
                            /*dataDump.AppendLine(id + "," + mrk + "," +
                                rectPos.x + "," + rectPos.y + "," +
                                rectSize.x + "," + rectSize.y + "," +
                                rectPosOther.x + "," + rectPosOther.y + "," +
                                rectSizeOther.x + "," + rectSizeOther.y + ",");*/
                            dataDump.AppendLine(id + "," + mrk + "," + rectPos.y + "," + rectPosOther.y);// This is all that's really needed
                        }
                    }
                    if (ClientSettings.AssetHelperDump && dataDump != null)
                    {
                        string dumpPath = Path.Combine(Program.ClientDataDumpDir, "SoloGateCards.txt");
                        try
                        {
                            Directory.CreateDirectory(Path.GetDirectoryName(dumpPath));
                        }
                        catch { }
                        try
                        {
                            File.WriteAllText(dumpPath, dataDump.ToStringLF());
                        }
                        catch { }
                    }
                    foreach (SoloGateCardEntry customSetting in SoloGates.Values)
                    {
                        if (!seenIds.Contains(customSetting.Id))
                        {
                            IntPtr newSetting = Import.Object.il2cpp_object_new(thumbSettingClassInfo.ptr);
                            if (newSetting == IntPtr.Zero)
                            {
                                continue;
                            }
                            int id = customSetting.Id;
                            thumbSettingCtor.Invoke(newSetting, new IntPtr[] { new IntPtr(&id) });
                            InjectSoloThumb(newSetting, customSetting);
                            settingsList.Add(newSetting);
                            if (cacheSetter != null)
                                cacheSetter.Invoke(settingsMapObj.ptr, new IntPtr[] { new IntPtr(&id), newSetting });
                            LogSoloThumbnail("Added gate=" + id + " card=" + customSetting.CardId + " cache=" + (cacheSetter != null));
                        }
                    }
                }
            }
        }

        static void InjectSoloBackground(IntPtr gameObject, int gateId)
        {
            if (ClientSettings.AssetHelperDump)
            {
                DumpSoloBackground(gameObject, gateId);
            }

            string filePath;
            if (SoloGateBackgroundPaths.TryGetValue(gateId, out filePath) && File.Exists(filePath))
            {
                bool includeInactive = true;
                IL2Object behavior = methodGetComponentInChildren.Invoke(gameObject, new IntPtr[] {
                    monoBehaviourClassInfo.IL2Typeof(), new IntPtr(&includeInactive) });
                if (behavior != null)
                {
                    IntPtr behaviorClass = Import.Object.il2cpp_object_get_class(behavior.ptr);
                    if (behaviorClass == imageClassInfo.ptr)
                    {
                        IntPtr sprite = SpriteFromPNG(filePath, Path.GetFileNameWithoutExtension(filePath));
                        if (sprite != IntPtr.Zero)
                        {
                            methodSetSprite.Invoke(behavior.ptr, new IntPtr[] { sprite });
                        }
                    }
                }
            }
        }

        static void DumpSoloBackground(IntPtr gameObject, int gateId)
        {
            string targetPath = Path.Combine(Program.ClientDataDumpDir, "SoloGateBackgrounds", gateId + ".png");
            if (!File.Exists(targetPath))
            {
                bool includeInactive = true;
                IL2Object behavior = methodGetComponentInChildren.Invoke(gameObject, new IntPtr[] {
                        monoBehaviourClassInfo.IL2Typeof(), new IntPtr(&includeInactive) });
                if (behavior != null)
                {
                    IntPtr behaviorClass = Import.Object.il2cpp_object_get_class(behavior.ptr);
                    if (behaviorClass == imageClassInfo.ptr)
                    {
                        IL2Object sprite = methodGetSprite.Invoke(behavior.ptr);
                        if (sprite != null)
                        {
                            IL2Object texture = methodGetTexture.Invoke(sprite.ptr);
                            if (texture != null)
                            {
                                byte[] buffer = TextureToPNG(texture.ptr);
                                if (buffer != null)
                                {
                                    try
                                    {
                                        Directory.CreateDirectory(Path.GetDirectoryName(targetPath));
                                    }
                                    catch { }
                                    try
                                    {
                                        File.WriteAllBytes(targetPath, buffer);
                                    }
                                    catch { }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
