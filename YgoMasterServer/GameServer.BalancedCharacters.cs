using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace YgoMaster
{
    partial class GameServer
    {
        sealed class BalancedEncounter
        {
            public int ChapterId;
            public int GateId;
            public string PlayerId;
            public string OpponentId;
        }
        readonly Dictionary<int, BalancedEncounter> balancedEncounters = new Dictionary<int, BalancedEncounter>();
        readonly HashSet<int> balancedReservedGates = new HashSet<int>();
        readonly Dictionary<int, int> balancedGoals = new Dictionary<int, int>();
        CharacterCatalog balancedCatalog;
        string balancedLoadError;
        DuelRunLogger balancedRunLogger;
        string balancedContentVersion;

        void BeginBalancedRun(Player player, DuelSettings settings)
        {
            if (balancedRunLogger == null) return;
            BalancedEncounter entry;
            bool balanced = balancedEncounters.TryGetValue(settings.chapter, out entry) && settings.GameMode == (int)GameMode.SoloSingle;
            balancedRunLogger.Begin(player, settings, balanced ? entry.PlayerId : null,
                balanced ? entry.OpponentId : null, balancedContentVersion, Path.GetFullPath(Path.Combine(dataDirectory, "..")));
        }

        bool IsBalancedChapter(int chapterId) { return balancedEncounters.ContainsKey(chapterId); }
        bool IsBalancedGoal(int chapterId) { return balancedGoals.ContainsKey(chapterId); }
        bool CanCompleteBalancedGoal(Player player, int chapterId)
        {
            if (!balancedGoals.ContainsKey(chapterId)) return false;
            return balancedEncounters.Values.Where(x => x.GateId == chapterId / 10000).All(x => {
                ChapterStatus status;
                return player.SoloChapters.TryGetValue(x.ChapterId, out status) && status == ChapterStatus.COMPLETE;
            });
        }
        bool IsReservedBalancedChapter(int chapterId) { return balancedReservedGates.Contains(chapterId / 10000); }

        void LoadBalancedCharacters()
        {
            balancedEncounters.Clear();
            balancedReservedGates.Clear();
            balancedGoals.Clear();
            balancedCatalog = null;
            balancedLoadError = null;
            balancedRunLogger = null;
            string root = Path.Combine(dataDirectory, "BalancedCharacters");
            string modeFile = Path.Combine(root, "Mode.json");
            if (!File.Exists(modeFile)) return;
            try
            {
                var mode = CharacterCatalog.Read(modeFile);
                if (!Utils.GetValue<bool>(mode, "enabled")) return;
                if (Utils.GetValue<int>(mode, "schemaVersion") != 1 ||
                    Utils.GetValue<string>(mode, "activeDeckRevision") != "source-v1")
                    throw new InvalidDataException("Unsupported mode schema or deck revision");
                var allocations = CharacterCatalog.Read(Path.Combine(root, "Ids.json"));
                foreach (var entry in Utils.GetDictionary(allocations, "characters"))
                    balancedReservedGates.Add(Utils.GetValue<int>((Dictionary<string, object>)entry.Value, "gateId"));
                List<object> selected;
                if (!Utils.TryGetValue(mode, "activeCharacterIds", out selected) || selected.Count < 2 || selected.Count > 15 ||
                    selected.Any(x => !(x is string))) throw new InvalidDataException("Invalid active character list");
                var catalog = CharacterCatalog.Load(root, selected.Cast<string>().ToList(), CardRare);
                var overlay = CharacterCatalog.Read(Path.Combine(root, "Generated", "Overlay.json"));
                if (Utils.GetValue<int>(overlay, "schemaVersion") != 1 ||
                    Utils.GetValue<string>(overlay, "contentVersion") != Utils.GetValue<string>(mode, "contentVersion"))
                    throw new InvalidDataException("Overlay version does not match mode");
                var hashes = Utils.GetDictionary(overlay, "deckFingerprints");
                foreach (string id in catalog.Ids)
                    if (Utils.GetValue<string>(hashes, id) != catalog.Fingerprint(id))
                        throw new InvalidDataException("Stale/tampered compiled deck: " + id);
                var gates = Utils.GetDictionary(overlay, "gate");
                var chapters = Utils.GetDictionary(overlay, "chapter");
                var existingGates = Utils.GetDictionary(SoloData, "gate");
                var existingChapters = Utils.GetDictionary(SoloData, "chapter");
                if (gates == null || chapters == null || existingGates == null || existingChapters == null)
                    throw new InvalidDataException("Invalid Solo overlay shape");
                foreach (var gate in gates)
                {
                    int gateId;
                    if (!int.TryParse(gate.Key, out gateId) || !balancedReservedGates.Contains(gateId) ||
                        existingGates.ContainsKey(gate.Key) || existingChapters.ContainsKey(gate.Key))
                        throw new InvalidDataException("Gate collision or unallocated gate");
                    var gateData = gate.Value as Dictionary<string, object>;
                    if (gateData == null || Utils.GetValue<int>(gateData, "category") != 1 ||
                        Utils.GetValue<int>(gateData, "parent_gate") != 0 || Utils.GetValue<int>(gateData, "view_gate") != 0 ||
                        Utils.GetValue<int>(gateData, "unlock_id") != 0)
                        throw new InvalidDataException("Invalid free-duel gate policy");
                }
                if (!new HashSet<string>(gates.Keys).SetEquals(chapters.Keys) ||
                    chapters.Any(x => !(x.Value is Dictionary<string, object>)))
                    throw new InvalidDataException("Chapter gate table differs from gate table");
                List<object> encounters;
                if (!Utils.TryGetValue(overlay, "encounters", out encounters)) throw new InvalidDataException("Missing encounters");
                var staged = new Dictionary<int, BalancedEncounter>();
                var templates = new Dictionary<int, DuelSettings>();
                int nextDeckId = SoloDuels.Values.SelectMany(x => x.Deck).Max(x => x.Id) + 1;
                foreach (var raw in encounters)
                {
                    var data = raw as Dictionary<string, object>;
                    if (data == null) throw new InvalidDataException("Invalid encounter");
                    var entry = new BalancedEncounter { ChapterId = Utils.GetValue<int>(data, "chapterId"),
                        GateId = Utils.GetValue<int>(data, "gateId"), PlayerId = Utils.GetValue<string>(data, "playerCharacterId"),
                        OpponentId = Utils.GetValue<string>(data, "opponentCharacterId") };
                    var chapterGate = Utils.GetDictionary(chapters, entry.GateId.ToString());
                    var chapter = Utils.GetDictionary(chapterGate, entry.ChapterId.ToString());
                    if (!gates.ContainsKey(entry.GateId.ToString()) || entry.ChapterId / 10000 != entry.GateId ||
                        chapter == null || SoloDuels.ContainsKey(entry.ChapterId) || staged.ContainsKey(entry.ChapterId) ||
                        entry.PlayerId == entry.OpponentId || !catalog.Ids.Contains(entry.PlayerId) || !catalog.Ids.Contains(entry.OpponentId))
                        throw new InvalidDataException("Invalid/colliding encounter");
                    var characterAllocations = Utils.GetDictionary(allocations, "characters");
                    if (Utils.GetValue<int>(Utils.GetDictionary(characterAllocations, entry.PlayerId), "gateId") != entry.GateId ||
                        Utils.GetValue<int>(chapter, "npc_id") != Utils.GetValue<int>(Utils.GetDictionary(characterAllocations, entry.OpponentId), "npcId") ||
                        Utils.GetValue<int>(chapter, "mydeck_set_id") != 0 || Utils.GetValue<int>(chapter, "set_id") != 1 ||
                        Utils.GetValue<int>(chapter, "unlock_id") != 0 || Utils.GetValue<int>(chapter, "anime") != 0 ||
                        !string.IsNullOrEmpty(Utils.GetValue<string>(chapter, "begin_sn")))
                        throw new InvalidDataException("Encounter does not match fixed free-duel policy");
                    var template = BuildBalancedTemplate(catalog, entry);
                    template.Deck[0].Id = nextDeckId++;
                    template.Deck[1].Id = nextDeckId++;
                    template.story_deck_id[0] = template.Deck[0].Id;
                    template.npc_deck_id = template.Deck[1].Id;
                    templates.Add(entry.ChapterId, template);
                    staged.Add(entry.ChapterId, entry);
                }
                int expectedCount = selected.Count * (selected.Count - 1);
                if (staged.Count != expectedCount || gates.Count != selected.Count ||
                    chapters.Sum(x => ((Dictionary<string, object>)x.Value).Count) != expectedCount + gates.Count ||
                    staged.Values.Select(x => x.PlayerId + "/" + x.OpponentId).Distinct().Count() != expectedCount)
                    throw new InvalidDataException("Incomplete encounter matrix");
                var stagedGoals = new Dictionary<int, int>();
                foreach (var gate in gates)
                {
                    int clearId = Utils.GetValue<int>((Dictionary<string, object>)gate.Value, "clear_chapter");
                    var chapterGate = Utils.GetDictionary(chapters, gate.Key);
                    var goal = Utils.GetDictionary(chapterGate, clearId.ToString());
                    int parent = goal == null ? 0 : Utils.GetValue<int>(goal, "parent_chapter");
                    if (clearId / 10000 != int.Parse(gate.Key) || clearId % 10000 != 9000 ||
                        staged.ContainsKey(clearId) || SoloDuels.ContainsKey(clearId) || goal == null ||
                        !staged.ContainsKey(parent) || staged[parent].GateId.ToString() != gate.Key ||
                        chapterGate.Count != selected.Count || Utils.GetValue<int>(goal, "npc_id") != 0 ||
                        Utils.GetValue<int>(goal, "set_id") != 0 || Utils.GetValue<int>(goal, "mydeck_set_id") != 0 ||
                        Utils.GetValue<int>(goal, "unlock_id") != 0 || Utils.GetValue<int>(goal, "anime") != 0 ||
                        !string.IsNullOrEmpty(Utils.GetValue<string>(goal, "begin_sn")))
                        throw new InvalidDataException("Balanced gate requires connected battles and a reward-free terminal goal");
                    // Walk back from Goal: every battle must appear once in a single
                    // connected chain. This rejects cycles, orphan branches and extra roots.
                    var visited = new HashSet<int>();
                    int current = parent;
                    while (current != 0)
                    {
                        BalancedEncounter encounter;
                        if (!visited.Add(current) || !staged.TryGetValue(current, out encounter) ||
                            encounter.GateId.ToString() != gate.Key)
                            throw new InvalidDataException("Disconnected/cyclic balanced chapter map");
                        current = Utils.GetValue<int>(Utils.GetDictionary(chapterGate, current.ToString()), "parent_chapter");
                    }
                    if (visited.Count != selected.Count - 1)
                        throw new InvalidDataException("Balanced chapter map does not connect every opponent");
                    stagedGoals.Add(clearId, parent);
                }
                // Commit only after every deck, gate and encounter validates.
                foreach (var gate in gates) existingGates.Add(gate.Key, gate.Value);
                foreach (var gate in chapters) existingChapters.Add(gate.Key, gate.Value);
                foreach (var duel in templates) SoloDuels.Add(duel.Key, duel.Value);
                foreach (var encounter in staged) balancedEncounters.Add(encounter.Key, encounter.Value);
                foreach (var goal in stagedGoals) balancedGoals.Add(goal.Key, goal.Value);
                balancedCatalog = catalog;
                balancedContentVersion = Utils.GetValue<string>(mode, "contentVersion");
                balancedRunLogger = new DuelRunLogger(Path.Combine(root, "Logs", "duels.jsonl"), false);
                Utils.LogInfo("Balanced Characters loaded: " + gates.Count + " gates / " + staged.Count + " encounters");
            }
            catch (Exception error)
            {
                balancedLoadError = error.Message;
                Utils.LogWarning("Balanced Characters disabled: " + balancedLoadError);
            }
        }

        static DuelSettings BuildBalancedTemplate(CharacterCatalog catalog, BalancedEncounter entry)
        {
            var settings = new DuelSettings { IsCustomDuel = true, chapter = entry.ChapterId,
                GameMode = (int)GameMode.SoloSingle, FirstPlayer = -1, cpu = 97, cpuflag = null,
                noshuffle = false, Type = 0, MyType = 0 };
            settings.Deck[0] = catalog.CreateDeck(entry.PlayerId);
            settings.Deck[1] = catalog.CreateDeck(entry.OpponentId);
            for (int i = 0; i < 2; i++) { settings.life[i] = 8000; settings.hnum[i] = 5; }
            settings.name[0] = catalog.Name(entry.PlayerId);
            settings.name[1] = catalog.Name(entry.OpponentId);
            settings.SetRequiredDefaults();
            return settings;
        }

        DuelSettings CreateBalancedDuelSettings(Player player, int chapterId, bool begin)
        {
            BalancedEncounter entry;
            if (balancedCatalog == null || !balancedEncounters.TryGetValue(chapterId, out entry)) return null;
            var settings = BuildBalancedTemplate(balancedCatalog, entry);
            var preview = SoloDuels[chapterId];
            settings.Deck[0].Id = preview.Deck[0].Id;
            settings.Deck[1].Id = preview.Deck[1].Id;
            settings.story_deck_id[0] = preview.story_deck_id[0];
            settings.npc_deck_id = preview.npc_deck_id;
            if (begin)
            {
                settings.FirstPlayer = rand.Next(2);
                settings.RandSeed = (uint)rand.Next(1, int.MaxValue);
                player.Duel.IsMyDeck = false;
                player.Duel.IsCustomSoloDuel = false;
            }
            if (!FixedDeckPolicy.Matches(settings.Deck[0], balancedCatalog.CreateDeck(entry.PlayerId)) ||
                !FixedDeckPolicy.Matches(settings.Deck[1], balancedCatalog.CreateDeck(entry.OpponentId)))
                throw new InvalidDataException("Trusted deck policy failed");
            return settings;
        }

        void EnsureBalancedChapterAccess(Player player)
        {
            foreach (int chapterId in balancedEncounters.Keys)
                if (!player.SoloChapters.ContainsKey(chapterId)) player.SoloChapters[chapterId] = ChapterStatus.OPEN;
        }
    }
}
