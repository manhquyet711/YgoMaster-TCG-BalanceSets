using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace YgoMaster
{
    partial class GameServer
    {
        // Each player gets one premade deck per TCG era format (e.g. "Era 12-14 Goat Format"),
        // already set to that format so the deck editor shows its ban list. The decks come from
        // Data/TCGCampaign/EraReferenceDecks.json (built by Tools/TCGCampaign/build_era_decks.py).
        // No cards are added to the collection: unowned cards show as missing.
        //
        // EraReferenceDecks.json in the player folder records which revision was given per deck:
        // - Not given yet: the deck is added.
        // - Given for an older revision and still present: its cards and format are refreshed.
        // - Given before but deleted or renamed by the player: it is not added back.
        const string EraReferenceDecksFile = "EraReferenceDecks.json";

        class EraReferenceDeck
        {
            public string Key;
            public string Name;
            public int RegulationId;
            public List<int> Main;
            public List<int> Extra;
        }

        string eraReferenceDeckRevision;
        List<EraReferenceDeck> eraReferenceDecks;

        void LoadEraReferenceDecks()
        {
            eraReferenceDecks = null;
            eraReferenceDeckRevision = null;
            string path = Path.Combine(dataDirectory, "TCGCampaign", "EraReferenceDecks.json");
            if (!File.Exists(path))
            {
                return;
            }
            try
            {
                Dictionary<string, object> data = MiniJSON.Json.DeserializeStripped(File.ReadAllText(path)) as Dictionary<string, object>;
                List<object> rows;
                if (data == null || !Utils.TryGetValue(data, "decks", out rows))
                {
                    Utils.LogWarning("Era reference decks file has no decks: " + path);
                    return;
                }
                var result = new List<EraReferenceDeck>();
                foreach (Dictionary<string, object> row in rows.OfType<Dictionary<string, object>>())
                {
                    var deck = new EraReferenceDeck()
                    {
                        Key = Utils.GetValue<string>(row, "key"),
                        Name = Utils.GetValue<string>(row, "name"),
                        RegulationId = Utils.GetValue<int>(row, "regulationId"),
                        Main = Utils.GetIntList(row, "main"),
                        Extra = Utils.GetIntList(row, "extra"),
                    };
                    if (string.IsNullOrEmpty(deck.Key) || string.IsNullOrEmpty(deck.Name) ||
                        !DeckInfo.RegulationNamesById.ContainsKey(deck.RegulationId))
                    {
                        Utils.LogWarning("Skipping era reference deck with missing key, name or regulation: " + deck.Key);
                        continue;
                    }
                    result.Add(deck);
                }
                eraReferenceDecks = result;
                eraReferenceDeckRevision = Utils.GetValue<string>(data, "revision", "1");
            }
            catch (Exception error)
            {
                Utils.LogWarning("Era reference decks were not loaded: " + error.Message);
            }
        }

        DeckInfo CreateEraReferenceDeck(EraReferenceDeck source)
        {
            DeckInfo deck = new DeckInfo();
            foreach (int card in source.Main) deck.MainDeckCards.Add(card);
            foreach (int card in source.Extra) deck.ExtraDeckCards.Add(card);
            deck.Name = source.Name;
            deck.RegulationId = source.RegulationId;
            deck.RegulationName = null;
            deck.FixupRegulation();
            return deck;
        }

        void SeedEraReferenceDecks(Player player)
        {
            if (eraReferenceDecks == null || eraReferenceDecks.Count == 0)
            {
                return;
            }
            try
            {
                string playerDir = GetPlayerDirectory(player);
                string markerPath = Path.Combine(playerDir, EraReferenceDecksFile);
                Dictionary<string, string> given = ReadGivenEraReferenceDecks(markerPath);
                string decksDir = GetDecksDirectory(player);
                bool changed = false;
                foreach (EraReferenceDeck source in eraReferenceDecks)
                {
                    string givenRevision;
                    bool wasGiven = given.TryGetValue(source.Key, out givenRevision);
                    if (wasGiven && givenRevision == eraReferenceDeckRevision)
                    {
                        continue;
                    }
                    DeckInfo existing = player.Decks.Values.FirstOrDefault(x =>
                        string.Equals(x.Name, source.Name, StringComparison.OrdinalIgnoreCase));
                    if (existing == null && !wasGiven)
                    {
                        DeckInfo deck = CreateEraReferenceDeck(source);
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
                        DeckInfo updated = CreateEraReferenceDeck(source);
                        existing.MainDeckCards.CopyFrom(updated.MainDeckCards);
                        existing.ExtraDeckCards.CopyFrom(updated.ExtraDeckCards);
                        existing.RegulationId = updated.RegulationId;
                        existing.RegulationName = updated.RegulationName;
                        existing.TimeEdited = Utils.GetEpochTime();
                        existing.Save();
                    }
                    given[source.Key] = eraReferenceDeckRevision;
                    changed = true;
                }
                if (changed)
                {
                    Utils.TryCreateDirectory(playerDir);
                    Dictionary<string, object> marker = new Dictionary<string, object>()
                    {
                        { "schemaVersion", 1 },
                        { "given", given.OrderBy(x => x.Key, StringComparer.Ordinal)
                            .ToDictionary(x => x.Key, x => (object)x.Value) }
                    };
                    File.WriteAllText(markerPath, MiniJSON.Json.Serialize(marker));
                }
            }
            catch (Exception error)
            {
                Utils.LogWarning("Era reference decks were not added: " + error.Message);
            }
        }

        static Dictionary<string, string> ReadGivenEraReferenceDecks(string markerPath)
        {
            Dictionary<string, string> result = new Dictionary<string, string>(StringComparer.Ordinal);
            if (!File.Exists(markerPath))
            {
                return result;
            }
            Dictionary<string, object> data = MiniJSON.Json.DeserializeStripped(File.ReadAllText(markerPath)) as Dictionary<string, object>;
            Dictionary<string, object> givenData = data != null ? Utils.GetDictionary(data, "given") : null;
            if (givenData != null)
            {
                foreach (KeyValuePair<string, object> entry in givenData)
                {
                    if (entry.Value is string)
                    {
                        result[entry.Key] = (string)entry.Value;
                    }
                }
            }
            return result;
        }
    }
}
