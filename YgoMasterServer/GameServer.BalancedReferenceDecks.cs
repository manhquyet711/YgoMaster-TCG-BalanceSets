using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace YgoMaster
{
    partial class GameServer
    {
        // Each player gets a read-only style copy of every balanced character deck in their
        // deck list, so they can look at the recipes from the start. No cards are added to
        // the collection: decks with unowned cards stay invalid for normal duels, so the TCG
        // campaign progression is unchanged. Each deck is added once; if the player deletes
        // or renames it, it is not added again (tracked in BalancedReferenceDecks.json).
        const string BalancedReferenceDeckPrefix = "Balanced - ";
        const string BalancedReferenceDecksFile = "BalancedReferenceDecks.json";

        static string BalancedReferenceDeckName(string displayName)
        {
            return BalancedReferenceDeckPrefix + displayName;
        }

        void SeedBalancedReferenceDecks(Player player)
        {
            if (balancedCatalog == null)
            {
                return;
            }
            try
            {
                string playerDir = GetPlayerDirectory(player);
                string markerPath = Path.Combine(playerDir, BalancedReferenceDecksFile);
                HashSet<string> seeded = ReadSeededBalancedReferenceDecks(markerPath);
                HashSet<string> existingNames = new HashSet<string>(
                    player.Decks.Values.Where(x => x.Name != null).Select(x => x.Name), StringComparer.OrdinalIgnoreCase);
                string decksDir = GetDecksDirectory(player);
                bool changed = false;
                foreach (string id in balancedCatalog.Ids)
                {
                    if (seeded.Contains(id))
                    {
                        continue;
                    }
                    string name = BalancedReferenceDeckName(balancedCatalog.Name(id));
                    if (!existingNames.Contains(name))
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
                        existingNames.Add(name);
                    }
                    seeded.Add(id);
                    changed = true;
                }
                if (changed)
                {
                    Utils.TryCreateDirectory(playerDir);
                    Dictionary<string, object> marker = new Dictionary<string, object>()
                    {
                        { "schemaVersion", 1 },
                        { "seeded", seeded.OrderBy(x => x, StringComparer.Ordinal).Cast<object>().ToList() }
                    };
                    File.WriteAllText(markerPath, MiniJSON.Json.Serialize(marker));
                }
            }
            catch (Exception error)
            {
                Utils.LogWarning("Balanced reference decks were not added: " + error.Message);
            }
        }

        static HashSet<string> ReadSeededBalancedReferenceDecks(string markerPath)
        {
            HashSet<string> result = new HashSet<string>(StringComparer.Ordinal);
            if (!File.Exists(markerPath))
            {
                return result;
            }
            Dictionary<string, object> data = MiniJSON.Json.DeserializeStripped(File.ReadAllText(markerPath)) as Dictionary<string, object>;
            List<object> ids;
            if (data != null && Utils.TryGetValue(data, "seeded", out ids))
            {
                foreach (string id in ids.OfType<string>())
                {
                    result.Add(id);
                }
            }
            return result;
        }
    }
}
