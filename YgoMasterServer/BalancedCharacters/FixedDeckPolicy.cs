using System;
using System.Collections.Generic;
using System.Linq;

namespace YgoMaster
{
    // Shared foundation for phase P3. Not yet connected to duel launch handlers.
    static class FixedDeckPolicy
    {
        public static bool Matches(DeckInfo actual, DeckInfo expected)
        {
            return actual != null && expected != null &&
                SameZone(actual.MainDeckCards, expected.MainDeckCards) &&
                SameZone(actual.ExtraDeckCards, expected.ExtraDeckCards) &&
                SameZone(actual.SideDeckCards, expected.SideDeckCards);
        }

        static bool SameZone(CardCollection actual, CardCollection expected)
        {
            if (actual.Count != expected.Count) return false;
            Dictionary<int, int> actualCounts = Counts(actual);
            Dictionary<int, int> expectedCounts = Counts(expected);
            return actualCounts.Count == expectedCounts.Count && expectedCounts.All(pair =>
                actualCounts.ContainsKey(pair.Key) && actualCounts[pair.Key] == pair.Value);
        }

        static Dictionary<int, int> Counts(CardCollection cards)
        {
            Dictionary<int, int> result = new Dictionary<int, int>();
            foreach (KeyValuePair<int, CardStyleRarity> card in cards.GetCollection())
            {
                int count;
                result.TryGetValue(card.Key, out count);
                result[card.Key] = count + 1;
            }
            return result;
        }
    }
}
