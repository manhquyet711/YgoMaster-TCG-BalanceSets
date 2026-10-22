using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

// Tests real server handlers and canonical decks, without launching listeners.
class ValidateBalancedIntegration
{
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;
    static Assembly assembly;
    static object Get(object obj, string name)
    {
        var field = obj.GetType().GetField(name, All);
        return field != null ? field.GetValue(obj) : obj.GetType().GetProperty(name, All).GetValue(obj, null);
    }
    static void Set(object obj, string name, object value) { obj.GetType().GetField(name, All).SetValue(obj, value); }
    static object Call(object obj, string name, params object[] args) { return obj.GetType().GetMethod(name, All).Invoke(obj, args); }
    static void Check(bool value, string text) { if (!value) throw new Exception("FAIL " + text); Console.WriteLine("PASS " + text); }
    static object Player()
    {
        var obj = Activator.CreateInstance(assembly.GetType("YgoMaster.Player", true), new object[] { (uint)123456789 });
        Set(obj, "Name", "Edited player name");
        return obj;
    }
    static object Request(object player, Dictionary<string, object> parameters)
    {
        var request = Activator.CreateInstance(assembly.GetType("YgoMaster.GameServerWebRequest", true), true);
        Set(request, "Player", player); Set(request, "ActParams", parameters);
        Set(request, "Response", new Dictionary<string, object>());
        return request;
    }
    static int Mode(string name) { return (int)Enum.Parse(assembly.GetType("YgoMaster.GameMode", true), name); }
    static void CopyTree(string source, string target)
    {
        Directory.CreateDirectory(target);
        foreach (string file in Directory.GetFiles(source)) File.Copy(file, Path.Combine(target, Path.GetFileName(file)));
        foreach (string dir in Directory.GetDirectories(source)) CopyTree(dir, Path.Combine(target, Path.GetFileName(dir)));
    }
    static void ValidateBadContent(object originalServer, string runtime, string operation)
    {
        string temp = Path.Combine(Path.GetTempPath(), "BalancedValidation-" + Guid.NewGuid().ToString("N"));
        try
        {
            string modeRoot = Path.Combine(temp, "BalancedCharacters");
            CopyTree(Path.Combine(runtime, "Data", "BalancedCharacters"), modeRoot);
            string target = operation == "disabled" ? Path.Combine(modeRoot, "Mode.json") :
                operation == "quantity" ? Path.Combine(modeRoot, "Decks", (string)Get(originalServer, "balancedDeckRevision"), "kaiba.json") :
                Path.Combine(modeRoot, "Generated", "Overlay.json");
            string text = File.ReadAllText(target);
            if (operation == "disabled") text = text.Replace("\"enabled\": true", "\"enabled\": false");
            else if (operation == "quantity") text = text.Replace("\"quantity\": 1", "\"quantity\": 4");
            else if (operation == "goal-parent") {
                int parent = (int)((IDictionary)Get(originalServer, "balancedGoals"))[20189000];
                text = text.Replace("\"parent_chapter\": " + parent, "\"parent_chapter\": 20189000");
            }
            else if (operation == "goal-root") text = text.Replace("\"clear_chapter\": 20189000", "\"clear_chapter\": 20180004");
            else text = text.Replace((string)Call(Get(originalServer, "balancedCatalog"), "Fingerprint", "kaiba"), new string('0', 64));
            File.WriteAllText(target, text);
            var server = Activator.CreateInstance(assembly.GetType("YgoMaster.GameServer", true), true);
            Set(server, "dataDirectory", Path.Combine(runtime, "Data"));
            Set(server, "CardRare", Get(originalServer, "CardRare"));
            Call(server, "LoadSolo");
            int originalDuels = ((IDictionary)Get(server, "SoloDuels")).Count;
            Set(server, "dataDirectory", temp);
            Call(server, "LoadBalancedCharacters");
            Check(((IDictionary)Get(server, "balancedEncounters")).Count == 0 &&
                ((IDictionary)Get(server, "SoloDuels")).Count == originalDuels,
                operation + ": mode adds no partial encounters and preserves base campaign");
            Check(operation == "disabled" ? Get(server, "balancedLoadError") == null : Get(server, "balancedLoadError") != null,
                operation + ": disabled/invalid content reported correctly");
        }
        finally
        {
            // Keep the tiny failing fixture for review; no recursive cleanup of computed paths.
            Console.WriteLine("Validation fixture: " + temp);
        }
    }
    static object Begin(object server, object player, int chapter, int mode, bool forged)
    {
        var rule = new Dictionary<string, object> { { "chapter", chapter }, { "GameMode", mode }, { "FirstPlayer", 77 } };
        if (forged) rule["duelStarterData"] = new Dictionary<string, object> {
            { "life", new List<object> { 1, 1 } }, { "hnum", new List<object> { 99, 99 } },
            { "noshuffle", true }, { "cpu", -100 }, { "Type", 4 }, { "name", new List<object> { "Forged", "Forged" } } };
        var request = Request(player, new Dictionary<string, object> { { "rule", rule } });
        Call(server, "Act_DuelBegin", request);
        return request;
    }
    static bool Matches(object first, object second)
    {
        return (bool)assembly.GetType("YgoMaster.FixedDeckPolicy", true).GetMethod("Matches", All).Invoke(null, new object[] { first, second });
    }
    static void ValidateReferenceDecks(object server)
    {
        string root = Path.Combine(Path.GetTempPath(), "BalancedReferenceDecks-" + Guid.NewGuid().ToString("N"));
        object oldMultiplayer = Get(server, "MultiplayerEnabled"), oldPlayers = Get(server, "playersDirectory");
        try
        {
            Set(server, "MultiplayerEnabled", true);
            Set(server, "playersDirectory", root);
            var player = Player();
            var catalog = Get(server, "balancedCatalog");
            var ids = ((IEnumerable)Get(catalog, "Ids")).Cast<string>().ToList();
            Call(server, "SeedBalancedReferenceDecks", player);
            var decks = (IDictionary)Get(player, "Decks");
            Check(decks.Count == ids.Count, "Every balanced character gets one reference deck");
            Check((int)Get(Get(player, "Cards"), "Count") == 0, "Reference decks add no cards to the collection");
            var regulation = Get(server, "Regulation");
            var deckType = assembly.GetType("YgoMaster.DeckInfo", true);
            var isValid = deckType.GetMethod("IsValid", All, null,
                new[] { assembly.GetType("YgoMaster.Player", true), typeof(int), typeof(Dictionary<string, object>) }, null);
            foreach (string id in ids)
            {
                string name = "Balanced - " + (string)Call(catalog, "Name", id);
                object deck = decks.Values.Cast<object>().Single(x => (string)Get(x, "Name") == name);
                Check(Matches(deck, Call(catalog, "CreateDeck", id)) && File.Exists((string)Get(deck, "File")),
                    "Reference deck saved with the canonical cards: " + id);
                Check(!(bool)isValid.Invoke(deck, new object[] { player, (int)Get(deck, "RegulationId"), regulation }),
                    "Reference deck cannot be used without owning its cards: " + id);
            }
            Call(server, "SeedBalancedReferenceDecks", player);
            Check(decks.Count == ids.Count, "Seeding again does not duplicate reference decks");
            object removed = decks.Values.Cast<object>().First();
            File.Delete((string)Get(removed, "File"));
            decks.Remove(Get(removed, "Id"));
            Call(server, "SeedBalancedReferenceDecks", player);
            Check(decks.Count == ids.Count - 1, "A deleted reference deck is not added back");
            // Upgrade path: a deck given for an older revision gets the new cards in place.
            string markerPath = Path.Combine(root, "123456789", "BalancedReferenceDecks.json");
            string kaibaName = "Balanced - " + (string)Call(catalog, "Name", "kaiba");
            object kaiba = decks.Values.Cast<object>().Single(x => (string)Get(x, "Name") == kaibaName);
            object kaibaMain = Get(kaiba, "MainDeckCards");
            Call(kaibaMain, "Clear");
            kaibaMain.GetType().GetMethod("Add", All).Invoke(kaibaMain, new object[] { 4007, Enum.ToObject(kaibaMain.GetType().GetMethod("Add", All).GetParameters()[1].ParameterType, 1) });
            string marker = File.ReadAllText(markerPath);
            File.WriteAllText(markerPath, marker.Replace("\"kaiba\":\"" + (string)Get(server, "balancedDeckRevision") + "\"", "\"kaiba\":\"source-v0-test\""));
            Call(server, "SeedBalancedReferenceDecks", player);
            Check(Matches(kaiba, Call(catalog, "CreateDeck", "kaiba")) && decks.Count == ids.Count - 1,
                "Reference deck from an older revision is updated in place without duplicates");
            File.WriteAllText(markerPath, "{\"seeded\":[\"kaiba\"]}");
            Call(server, "SeedBalancedReferenceDecks", player);
            Check(File.ReadAllText(markerPath).Contains("\"kaiba\":\"" + (string)Get(server, "balancedDeckRevision") + "\""),
                "First-release marker files are read and upgraded");
        }
        finally
        {
            Set(server, "MultiplayerEnabled", oldMultiplayer);
            Set(server, "playersDirectory", oldPlayers);
            try { Directory.Delete(root, true); } catch { }
        }
    }
    static void ValidateLaunch(object request, object expected, string playerName, string opponentName)
    {
        var response = (Dictionary<string, object>)Get(request, "Response");
        Check(response.ContainsKey("Duel"), "Balanced launch emitted a duel");
        var active = Get(Get(request, "Player"), "ActiveDuelSettings");
        var decks = (Array)Get(active, "Deck"); var templateDecks = (Array)Get(expected, "Deck");
        Check(Matches(decks.GetValue(0), templateDecks.GetValue(0)) && Matches(decks.GetValue(1), templateDecks.GetValue(1)), "Exact canonical decks survived forged launch data");
        Check(((int[])Get(active, "life")).Take(2).All(x => x == 8000) && ((int[])Get(active, "hnum")).Take(2).All(x => x == 5), "Trusted life and starting hands enforced");
        Check(!(bool)Get(active, "noshuffle") && (int)Get(active, "Type") == 0 && (int)Get(active, "cpu") == 97, "Trusted shuffle, duel type and CPU enforced");
        Check((int)Get(active, "FirstPlayer") >= 0 && (int)Get(active, "FirstPlayer") <= 1 && (uint)Get(active, "RandSeed") != 0, "Client FirstPlayer override rejected and fresh seed selected");
        Check(((string[])Get(active, "name"))[0] == playerName && ((string[])Get(active, "name"))[1] == opponentName, "Character names preserved");
    }
    static int Main(string[] args)
    {
        try
        {
            string runtime = Path.GetFullPath(args[0]); Environment.CurrentDirectory = runtime;
            assembly = Assembly.LoadFrom(Path.Combine(runtime, "YgoMaster.exe"));
            var server = Activator.CreateInstance(assembly.GetType("YgoMaster.GameServer", true), true);
            Call(server, "LoadSettings");
            Check(Get(server, "balancedLoadError") == null, "Balanced mode loaded without errors");
            string runLog = Path.Combine(Path.GetTempPath(), "BalancedRuns-" + Guid.NewGuid().ToString("N"), "duels.jsonl");
            Set(server, "balancedRunLogger", Activator.CreateInstance(assembly.GetType("YgoMaster.DuelRunLogger", true),
                new object[] { runLog, true }));
            var encounters = (IDictionary)Get(server, "balancedEncounters");
            int characterCount = ((IEnumerable)Get(Get(server, "balancedCatalog"), "Ids")).Cast<object>().Count();
            Check(encounters.Count == characterCount * (characterCount - 1), "Complete directed encounter matrix registered");
            var duels = (IDictionary)Get(server, "SoloDuels");
            int chapter = 0;
            foreach (DictionaryEntry item in encounters)
                if ((string)Get(item.Value, "PlayerId") == "kaiba" && (string)Get(item.Value, "OpponentId") == "joey") chapter = (int)item.Key;
            Check(chapter > 0, "Kaiba player encounter found");
            var goals = (IDictionary)Get(server, "balancedGoals");
            Check(goals.Count == characterCount, "Each character gate has a separate terminal goal");
            int goal = chapter / 10000 * 10000 + 9000;
            Check(goals.Contains(goal) && encounters.Contains((int)goals[goal]), "Terminal goal is connected to a battle");
            var gateMaster = (Dictionary<string, object>)((Dictionary<string, object>)Get(server, "SoloData"))["gate"];
            var gateData = (Dictionary<string, object>)gateMaster[(chapter / 10000).ToString()];
            Check(Convert.ToInt32(gateData["clear_chapter"]) == goal && goal != chapter, "Native goal selection cannot consume the battle node");
            var goalPlayer = Player();
            var lockedGoal = Request(goalPlayer, new Dictionary<string, object> { { "chapter", goal } });
            Call(server, "Act_SoloStart", lockedGoal);
            Check((int)Get(lockedGoal, "ResultCode") != 0 && !((IDictionary)Get(goalPlayer, "SoloChapters")).Contains(goal), "Goal cannot be completed before winning its battle");
            var forgedGoal = Begin(server, goalPlayer, goal, Mode("SoloSingle"), true);
            Check((int)Get(forgedGoal, "ResultCode") != 0 && !((Dictionary<string, object>)Get(forgedGoal, "Response")).ContainsKey("Duel"), "Goal cannot be forged into a custom duel");
            var won = Request(goalPlayer, new Dictionary<string, object>());
            Call(server, "SoloUpdateChapterStatus", won, chapter,
                Enum.Parse(assembly.GetType("YgoMaster.DuelResultType", true), "Win"),
                Enum.Parse(assembly.GetType("YgoMaster.DuelFinishType", true), "None"));
            if (characterCount > 2)
                Check(!(bool)Call(server, "CanCompleteBalancedGoal", goalPlayer, goal), "One victory cannot clear an unfinished character gate");
            foreach (DictionaryEntry item in encounters)
                if ((int)Get(item.Value, "GateId") == chapter / 10000)
                    Call(server, "SoloUpdateChapterStatus", won, (int)item.Key,
                        Enum.Parse(assembly.GetType("YgoMaster.DuelResultType", true), "Win"),
                        Enum.Parse(assembly.GetType("YgoMaster.DuelFinishType", true), "None"));
            Check((bool)Call(server, "CanCompleteBalancedGoal", goalPlayer, goal), "Winning every opponent unlocks the terminal goal");
            var openGoal = Request(goalPlayer, new Dictionary<string, object> { { "chapter", goal } });
            Call(server, "Act_SoloStart", openGoal);
            var goalResponse = (Dictionary<string, object>)Get(openGoal, "Response");
            var goalSolo = (Dictionary<string, object>)goalResponse["Solo"];
            var goalResult = (Dictionary<string, object>)goalSolo["Result"];
            Check((int)Get(openGoal, "ResultCode") == 0 && ((IDictionary)Get(goalPlayer, "SoloChapters")).Contains(goal) &&
                ((IList)goalResult["rewards"]).Count == 0 && !goalResponse.ContainsKey("Duel"), "Unlocked goal completes without rewards or a duel");
            object template = duels[chapter]; var player = Player();
            Call(server, "EnsureBalancedChapterAccess", player);
            Check(((IDictionary)Get(player, "SoloChapters")).Count == encounters.Count, "All opponent battles open immediately; goals remain locked");
            Set(player, "SoloGateId", chapter / 10000);
            var deckInfoRequest = Request(player, new Dictionary<string, object>());
            Call(server, "WriteSolo_deck_info", deckInfoRequest);
            var soloInfo = (Dictionary<string, object>)((Dictionary<string, object>)Get(deckInfoRequest, "Response"))["Solo"];
            var deckInfo = (Dictionary<string, object>)soloInfo["deck_info"];
            Check((bool)deckInfo["valid"] && !(bool)deckInfo["possession"], "Gate UI exposes a valid loaner without requiring owned cards");
            var detailRequest = Request(player, new Dictionary<string, object> { { "chapter", chapter } });
            Call(server, "Act_SoloDetail", detailRequest);
            var detailSolo = (Dictionary<string, object>)((Dictionary<string, object>)Get(detailRequest, "Response"))["Solo"];
            var detailChapters = (Dictionary<string, object>)detailSolo["chapter"];
            var detail = (Dictionary<string, object>)detailChapters[chapter.ToString()];
            Check((int)detail["story_deck_id"] > 0 && (int)detail["npc_deck_id"] > 0 &&
                detail.ContainsKey("story_deck") && detail.ContainsKey("npc_deck"), "Solo detail registers player/opponent deck recipes with valid IDs");
            var playerDuel = Get(player, "Duel"); Set(playerDuel, "IsMyDeck", true);
            var preview = Call(server, "CreateSoloDuelSettingsInstance", player, chapter);
            Check(Matches(((Array)Get(preview, "Deck")).GetValue(0), ((Array)Get(template, "Deck")).GetValue(0)), "My Deck route returns trusted loaner without card ownership");
            var previewCards = Get(((Array)Get(preview, "Deck")).GetValue(0), "MainDeckCards");
            Call(previewCards, "Clear");
            Check((int)Get(Get(((Array)Get(template, "Deck")).GetValue(0), "MainDeckCards"), "Count") == 40, "Mutating preview cannot mutate trusted template");
            ValidateLaunch(Begin(server, player, chapter, Mode("SoloSingle"), true), template, "Kaiba", "Joey");
            ValidateLaunch(Begin(server, Player(), chapter, Mode("SoloSingle"), false), template, "Kaiba", "Joey");
            int beforeEnd = File.ReadAllLines(runLog).Length;
            var endRequest = Request(player, new Dictionary<string, object> { { "params", new Dictionary<string, object> {
                { "res", 1 }, { "finish", 1 }, { "turn", 7 } } } });
            Call(server, "Act_DuelEnd", endRequest);
            Call(server, "Act_DuelEnd", endRequest);
            Check(File.ReadAllLines(runLog).Length == beforeEnd + 1, "Actual Duel.end handler records one terminal result despite duplicate requests");
            string recordedEnd = File.ReadAllLines(runLog).Last();
            Check(recordedEnd.Contains("\"result\":\"win\"") && recordedEnd.Contains("\"turns\":7"), "Terminal evidence includes reported result and turns");
            var interruptedPlayer = Player();
            Begin(server, interruptedPlayer, chapter, Mode("SoloSingle"), false);
            Call(Get(server, "balancedRunLogger"), "End", interruptedPlayer, chapter,
                Enum.Parse(assembly.GetType("YgoMaster.DuelResultType", true), "Lose"),
                Enum.Parse(assembly.GetType("YgoMaster.DuelFinishType", true), "FinishDisconnect"), 0);
            string disconnected = File.ReadAllLines(runLog).Last();
            Check(disconnected.Contains("\"result\":\"interrupted\"") && disconnected.Contains("\"eligibleForWinRate\":false"),
                "Disconnect is excluded from gameplay losses and win rates");
            var restartedPlayer = Player();
            Begin(server, restartedPlayer, chapter, Mode("SoloSingle"), false);
            int beforeRestart = File.ReadAllLines(runLog).Length;
            Begin(server, restartedPlayer, chapter, Mode("SoloSingle"), false);
            Check(File.ReadAllLines(runLog).Length == beforeRestart + 2 && File.ReadAllText(runLog).Contains("another_duel_started"),
                "Starting another duel closes the previous run as interrupted and links a fresh run");
            Check(!File.ReadAllText(runLog).Contains("123456789") && !File.ReadAllText(runLog).Contains("Edited player name"),
                "Run evidence omits account codes and personal player names");
            var catalog = Get(server, "balancedCatalog");
            foreach (DictionaryEntry item in encounters)
            {
                var testPlayer = Player();
                Call(server, "EnsureBalancedChapterAccess", testPlayer);
                int id = (int)item.Key;
                Set(testPlayer, "SoloGateId", id / 10000);
                var matrixDetailRequest = Request(testPlayer, new Dictionary<string, object> { { "chapter", id } });
                Call(server, "Act_SoloDetail", matrixDetailRequest);
                var matrixSolo = (Dictionary<string, object>)((Dictionary<string, object>)Get(matrixDetailRequest, "Response"))["Solo"];
                var matrixDetail = (Dictionary<string, object>)((Dictionary<string, object>)matrixSolo["chapter"])[id.ToString()];
                if (Convert.ToInt32(matrixDetail["story_deck_id"]) <= 0 || Convert.ToInt32(matrixDetail["npc_deck_id"]) <= 0 ||
                    !matrixDetail.ContainsKey("story_deck") || !matrixDetail.ContainsKey("npc_deck"))
                    throw new Exception("Missing matrix deck recipes: " + id);
                var result = Begin(server, testPlayer, id, Mode("SoloSingle"), true);
                var active = Get(testPlayer, "ActiveDuelSettings");
                var actualDecks = (Array)Get(active, "Deck");
                string p = (string)Get(item.Value, "PlayerId"), o = (string)Get(item.Value, "OpponentId");
                if ((int)Get(result, "ResultCode") != 0 ||
                    !((Dictionary<string, object>)Get(result, "Response")).ContainsKey("Duel") ||
                    !Matches(actualDecks.GetValue(0), Call(catalog, "CreateDeck", p)) ||
                    !Matches(actualDecks.GetValue(1), Call(catalog, "CreateDeck", o)) ||
                    ((string[])Get(active, "name"))[0] != (string)Call(catalog, "Name", p) ||
                    ((string[])Get(active, "name"))[1] != (string)Call(catalog, "Name", o))
                    throw new Exception("Matrix launch mismatch: " + p + "/" + o);
            }
            Check(true, "Every directed encounter exposes deck recipes and launches exact canonical decks/names through real handlers");
            var invalidMode = Begin(server, Player(), chapter, Mode("Room"), true);
            Check((int)Get(invalidMode, "ResultCode") != 0 && !((Dictionary<string, object>)Get(invalidMode, "Response")).ContainsKey("Duel"), "Reserved chapter cannot be launched as a room/custom bypass");
            var invalidChapter = Begin(server, Player(), chapter + 999, Mode("SoloSingle"), true);
            Check((int)Get(invalidChapter, "ResultCode") != 0 && !((Dictionary<string, object>)Get(invalidChapter, "Response")).ContainsKey("Duel"), "Unknown reserved chapter fails closed");
            var ordinary = Begin(server, Player(), 0, Mode("SoloSingle"), true);
            Check(((Dictionary<string, object>)Get(ordinary, "Response")).ContainsKey("Duel"), "Ordinary custom-duel route remains available outside balanced IDs");
            var completed = Enum.Parse(assembly.GetType("YgoMaster.ChapterStatus", true), "COMPLETE");
            ((IDictionary)Get(player, "SoloChapters"))[chapter] = completed;
            var afterComplete = Call(server, "GetSoloDuelSettings", player, chapter);
            Check(Matches(((Array)Get(afterComplete, "Deck")).GetValue(0), ((Array)Get(template, "Deck")).GetValue(0)), "Completed balanced chapters retain fixed decks");
            string customRoot = Path.Combine(Path.GetTempPath(), "BalancedCustomOverride-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(customRoot);
            string customFile = Path.Combine(customRoot, "CustomDuel.json");
            File.WriteAllText(customFile, "{\"targetChapterId\":" + chapter + ",\"Deck\":[]}");
            object oldDataDir = Get(server, "dataDirectory");
            try
            {
                Set(server, "dataDirectory", customRoot);
                Set(server, "CustomDuelSettings", Activator.CreateInstance(assembly.GetType("YgoMaster.DuelSettings", true), true));
                Set(server, "CustomDuelLastModified", new FileInfo(customFile).LastWriteTime);
                var customAttempt = Call(server, "GetSoloDuelSettings", player, chapter);
                Check(Matches(((Array)Get(customAttempt, "Deck")).GetValue(0), ((Array)Get(template, "Deck")).GetValue(0)),
                    "Completed chapter ignores targeted CustomDuel.json and cached custom settings");
            }
            finally { Set(server, "dataDirectory", oldDataDir); }
            ValidateReferenceDecks(server);
            ValidateBadContent(server, runtime, "disabled");
            ValidateBadContent(server, runtime, "quantity");
            ValidateBadContent(server, runtime, "fingerprint");
            ValidateBadContent(server, runtime, "goal-parent");
            ValidateBadContent(server, runtime, "goal-root");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
