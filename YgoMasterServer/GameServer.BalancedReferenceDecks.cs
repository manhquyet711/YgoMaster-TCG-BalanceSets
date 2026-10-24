using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace YgoMaster
{
    partial class GameServer
    {
        // Each player gets a copy of every balanced character deck in their deck list, so they
        // can look at the recipes from the start. No cards are added to the collection: decks
        // with unowned cards stay invalid for normal duels, so the TCG campaign is unchanged.
        //
        // BalancedReferenceDecks.json records which deck revision was given for each character.
        // - Not given yet: the deck is added.
        // - Given for an older revision and still present: its cards are replaced with the new list.
        // - Given before but deleted or renamed by the player: it is not added back.
        // A deck the player made with the same name, without it being given, is never touched.
        const string BalancedReferenceDeckPrefix = "Balanced - ";
        const string BalancedReferenceDecksFile = "BalancedReferenceDecks.json";

        static string BalancedReferenceDeckName(string displayName)
        {
            return BalancedReferenceDeckPrefix + displayName;
        }

        void SeedBalancedReferenceDecks(Player player)
        {
            // One reference deck per character of every loaded set, named with the set's prefix
            // ("Balanced - ", "Goat Era - ", "Royale - ") so the deck list groups them.
            foreach (var set in balancedSets)
            {
                SeedBalancedReferenceDecks(player, set.Catalog, set.Revision, set.DeckPrefix ?? BalancedReferenceDeckPrefix);
            }
        }

        void SeedBalancedReferenceDecks(Player player, CharacterCatalog balancedCatalog, string balancedDeckRevision, string prefix)
        {
            if (balancedCatalog == null || string.IsNullOrEmpty(balancedDeckRevision))
            {
                return;
            }
            try
            {
                string playerDir = GetPlayerDirectory(player);
                string markerPath = Path.Combine(playerDir, BalancedReferenceDecksFile);
                Dictionary<string, string> given = ReadGivenBalancedReferenceDecks(markerPath);
                string decksDir = GetDecksDirectory(player);
                bool changed = false;
                foreach (string id in balancedCatalog.Ids)
                {
                    // Marker = revision plus the deck's fingerprint, so a deck tuned within the same revision
                    // (for example a balance round) also updates. Older markers hold the revision only.
                    string current = balancedDeckRevision + ":" + balancedCatalog.Fingerprint(id);
                    string givenRevision;
                    bool wasGiven = given.TryGetValue(id, out givenRevision);
                    if (wasGiven && givenRevision == current)
                    {
                        continue;
                    }
                    string name = prefix + balancedCatalog.Name(id);
                    DeckInfo existing = player.Decks.Values.FirstOrDefault(x =>
                        string.Equals(x.Name, name, StringComparison.OrdinalIgnoreCase));
                    if (existing == null && !wasGiven)
                    {
                        DeckInfo deck = balancedCatalog.CreateDeck(id);
                        deck.Name = name;
                        deck.RegulationId = DeckInfo.DefaultRegulationId;
                        deck.FixupRegulation();
                        deck.TimeCreated = Utils.GetEpochTime();
                        deck.TimeEdited = deck.TimeCreated;
                        deck.Accessory.Sanitize(player);
                        deck.GetNewFilePath(decksDir);
                        while ((deck.Id = player.NextDeckUId++) == DeckInfo.TradeDeckId)
                        {
                        }
                        // Register before writing so the local deck folder watcher sees a known file.
                        player.Decks[deck.Id] = deck;
                        deck.Save();
                    }
                    else if (existing != null && wasGiven)
                    {
                        // Newer revision of a deck we gave earlier: replace only the card lists.
                        DeckInfo updated = balancedCatalog.CreateDeck(id);
                        existing.MainDeckCards.CopyFrom(updated.MainDeckCards);
                        existing.ExtraDeckCards.CopyFrom(updated.ExtraDeckCards);
                        existing.SideDeckCards.CopyFrom(updated.SideDeckCards);
                        existing.TimeEdited = Utils.GetEpochTime();
                        existing.Save();
                    }
                    given[id] = current;
                    changed = true;
                }
                if (changed)
                {
                    Utils.TryCreateDirectory(playerDir);
                    Dictionary<string, object> marker = new Dictionary<string, object>()
                    {
                        { "schemaVersion", 2 },
                        { "given", given.OrderBy(x => x.Key, StringComparer.Ordinal)
                            .ToDictionary(x => x.Key, x => (object)x.Value) }
                    };
                    File.WriteAllText(markerPath, MiniJSON.Json.Serialize(marker));
                }
            }
            catch (Exception error)
            {
                Utils.LogWarning("Balanced reference decks were not added: " + error.Message);
            }
        }

        static Dictionary<string, string> ReadGivenBalancedReferenceDecks(string markerPath)
        {
            Dictionary<string, string> result = new Dictionary<string, string>(StringComparer.Ordinal);
            if (!File.Exists(markerPath))
            {
                return result;
            }
            Dictionary<string, object> data = MiniJSON.Json.DeserializeStripped(File.ReadAllText(markerPath)) as Dictionary<string, object>;
            if (data == null)
            {
                return result;
            }
            Dictionary<string, object> given = Utils.GetDictionary(data, "given");
            if (given != null)
            {
                foreach (KeyValuePair<string, object> entry in given)
                {
                    if (entry.Value is string)
                    {
                        result[entry.Key] = (string)entry.Value;
                    }
                }
            }
            // Schema 1 (first release) listed IDs only; those decks were all source-v1.
            List<object> seeded;
            if (Utils.TryGetValue(data, "seeded", out seeded))
            {
                foreach (string id in seeded.OfType<string>())
                {
                    if (!result.ContainsKey(id))
                    {
                        result[id] = CharacterCatalog.FirstRevision;
                    }
                }
            }
            return result;
        }
    }
}
