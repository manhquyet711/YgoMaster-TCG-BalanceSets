using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace YgoMaster
{
    // Trusted, validated deck templates. Callers receive independent copies.
    sealed class CharacterCatalog
    {
        readonly Dictionary<string, DeckInfo> decks = new Dictionary<string, DeckInfo>();
        readonly Dictionary<string, string> names = new Dictionary<string, string>();
        readonly Dictionary<string, string> fingerprints = new Dictionary<string, string>();
        public IEnumerable<string> Ids { get { return decks.Keys; } }
        public string Name(string id) { return names[id]; }
        public string Fingerprint(string id) { return fingerprints[id]; }
        public DeckInfo CreateDeck(string id)
        {
            DeckInfo result = new DeckInfo();
            result.FromDictionary(decks[id].ToDictionary(true), true);
            result.Name = names[id];
            return result;
        }

        public static Dictionary<string, object> Read(string path)
        {
            var data = MiniJSON.Json.DeserializeStripped(File.ReadAllText(path)) as Dictionary<string, object>;
            if (data == null) throw new InvalidDataException("Invalid JSON object: " + path);
            return data;
        }

        static int StrictInt(object value)
        {
            if (!(value is int) && !(value is long)) throw new InvalidDataException("Expected an integer");
            return checked(Convert.ToInt32(value));
        }

        public const string FirstRevision = "source-v1";

        // Revision names are "source-v<number>". v1 sources predate revisions and stay at the
        // SourceDecks root; later revisions use SourceDecks/<revision>.
        public static bool IsValidRevision(string revision)
        {
            int number;
            return revision != null && revision.StartsWith("source-v") &&
                int.TryParse(revision.Substring("source-v".Length), out number) && number >= 1 &&
                revision == "source-v" + number;
        }

        public static string SourceDeckPath(string root, string revision, string id)
        {
            return revision == FirstRevision ? Path.Combine(root, "SourceDecks", id + ".json") :
                Path.Combine(root, "SourceDecks", revision, id + ".json");
        }

        public static CharacterCatalog Load(string root, List<string> selected, Dictionary<int, int> knownCards)
        {
            return Load(root, selected, knownCards, FirstRevision);
        }

        public static CharacterCatalog Load(string root, List<string> selected, Dictionary<int, int> knownCards, string revision)
        {
            if (!IsValidRevision(revision))
                throw new InvalidDataException("Unsupported deck revision");
            if (selected == null || selected.Count < 2 || selected.Distinct().Count() != selected.Count)
                throw new InvalidDataException("Select at least two distinct characters");
            var roster = MiniJSON.Json.DeserializeStripped(File.ReadAllText(Path.Combine(root, "Roster.json"))) as List<object>;
            if (roster == null) throw new InvalidDataException("Roster missing");
            var result = new CharacterCatalog();
            foreach (string id in selected)
            {
                if (string.IsNullOrEmpty(id) || id.Any(c => !(char.IsLetterOrDigit(c) || c == '_')))
                    throw new InvalidDataException("Unsafe character ID");
                var matches = roster.OfType<Dictionary<string, object>>().Where(x => Utils.GetValue<string>(x, "id") == id).ToList();
                if (matches.Count != 1) throw new InvalidDataException("Unknown or duplicate roster ID: " + id);
                var source = Read(SourceDeckPath(root, revision, id));
                // "designed": AI-built sets checked by their own tool (Tools/BalancedCharacters/goat_set.py)
                string verification = Utils.GetValue<string>(source, "verificationStatus");
                if (verification != "photo-verified" && verification != "designed")
                    throw new InvalidDataException("Unreviewed source photo: " + id);
                var canonical = Read(Path.Combine(root, "Decks", revision, id + ".json"));
                if (Utils.GetValue<int>(canonical, "schemaVersion") != 1 ||
                    Utils.GetValue<string>(canonical, "characterId") != id ||
                    Utils.GetValue<string>(canonical, "revision") != revision)
                    throw new InvalidDataException("Invalid canonical deck identity: " + id);
                if (Utils.GetValue<int>(canonical, "expectedMainCount") != Utils.GetValue<int>(source, "expectedMainCount") ||
                    Utils.GetValue<int>(canonical, "expectedExtraCount") != Utils.GetValue<int>(source, "expectedExtraCount"))
                    throw new InvalidDataException("Canonical counts differ from reviewed source: " + id);
                DeckInfo deck = new DeckInfo();
                CardCollection[] collections = { deck.MainDeckCards, deck.ExtraDeckCards, deck.SideDeckCards };
                string[] zones = { "main", "extra", "side" };
                Dictionary<int, int> total = new Dictionary<int, int>();
                for (int i = 0; i < zones.Length; i++)
                {
                    List<object> entries;
                    if (!Utils.TryGetValue(canonical, zones[i], out entries)) throw new InvalidDataException("Missing deck zone");
                    HashSet<int> seen = new HashSet<int>();
                    foreach (object obj in entries)
                    {
                        var entry = obj as Dictionary<string, object>;
                        if (entry == null) throw new InvalidDataException("Invalid card entry");
                        int cardId = StrictInt(entry["cardId"]), quantity = StrictInt(entry["quantity"]);
                        if (cardId <= 0 || !knownCards.ContainsKey(cardId) || quantity < 1 || quantity > 3 || !seen.Add(cardId))
                            throw new InvalidDataException("Invalid card or quantity: " + id);
                        if (!total.ContainsKey(cardId)) total[cardId] = 0;
                        total[cardId] += quantity;
                        if (total[cardId] > 3) throw new InvalidDataException("More than three copies across zones");
                        for (int n = 0; n < quantity; n++) collections[i].Add(cardId);
                    }
                    int expected = i == 0 ? Utils.GetValue<int>(source, "expectedMainCount") :
                        i == 1 ? Utils.GetValue<int>(source, "expectedExtraCount") : 0;
                    if (collections[i].Count != expected ||
                        (i == 0 && (expected < 40 || expected > 60)) || (i == 1 && expected > 15))
                        throw new InvalidDataException("Deck count differs from reviewed source: " + id);
                }
                result.decks.Add(id, deck);
                result.names.Add(id, Utils.GetValue<string>(matches[0], "displayName"));
                result.fingerprints.Add(id, ComputeFingerprint(deck));
            }
            return result;
        }

        public static string ComputeFingerprint(DeckInfo deck)
        {
            // Match content.py's compact, sorted JSON fingerprint exactly.
            StringBuilder value = new StringBuilder("{");
            string[] zones = { "extra", "main", "side" };
            CardCollection[] cards = { deck.ExtraDeckCards, deck.MainDeckCards, deck.SideDeckCards };
            for (int i = 0; i < zones.Length; i++)
            {
                if (i != 0) value.Append(',');
                value.Append('"').Append(zones[i]).Append("\":[");
                bool first = true;
                foreach (var group in cards[i].GetCollection().GroupBy(x => x.Key).OrderBy(x => x.Key))
                {
                    if (!first) value.Append(',');
                    first = false;
                    value.Append('[').Append(group.Key).Append(',').Append(group.Count()).Append(']');
                }
                value.Append(']');
            }
            value.Append('}');
            using (SHA256 sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value.ToString()))).Replace("-", "").ToLowerInvariant();
        }
    }
}
