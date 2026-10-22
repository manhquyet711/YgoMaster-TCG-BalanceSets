using System;
using System.IO;
using System.Reflection;

// Exercise the real compiled server policy without opening an HTTP listener.
class ValidateBalancedCharacters
{
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;
    static Assembly assembly;
    static Type deckType;
    static object Deck(int[] main, int[] extra, int[] side, int finish)
    {
        object deck = Activator.CreateInstance(deckType, true);
        string[] zones = { "MainDeckCards", "ExtraDeckCards", "SideDeckCards" };
        int[][] lists = { main, extra, side };
        for (int i = 0; i < zones.Length; i++)
        {
            object cards = deckType.GetProperty(zones[i], All).GetValue(deck, null);
            MethodInfo add = cards.GetType().GetMethod("Add", All);
            foreach (int id in lists[i])
                add.Invoke(cards, new object[] { id, Enum.ToObject(assembly.GetType("YgoMaster.CardStyleRarity", true), finish) });
        }
        return deck;
    }
    static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception("FAIL " + message);
        Console.WriteLine("PASS " + message);
    }
    static int Main(string[] args)
    {
        try
        {
            assembly = Assembly.LoadFrom(Path.Combine(Path.GetFullPath(args[0]), "YgoMaster.exe"));
            deckType = assembly.GetType("YgoMaster.DeckInfo", true);
            MethodInfo matches = assembly.GetType("YgoMaster.FixedDeckPolicy", true).GetMethod("Matches", All);
            Func<object, object, bool> equal = (a, b) => (bool)matches.Invoke(null, new object[] { a, b });
            int[] none = new int[0];
            object expected = Deck(new int[] { 3801, 3801, 4041 }, new int[] { 4386 }, none, 1);
            Check(equal(Deck(new int[] { 4041, 3801, 3801 }, new int[] { 4386 }, none, 1), expected), "Order does not change identity");
            Check(equal(Deck(new int[] { 3801, 4041, 3801 }, new int[] { 4386 }, none, 3), expected), "Cosmetic finish does not change identity");
            Check(!equal(Deck(new int[] { 3801, 4041, 4041 }, new int[] { 4386 }, none, 1), expected), "Changed quantities rejected even at same total");
            Check(!equal(Deck(new int[] { 3801, 3801, 4041, 4842 }, new int[] { 4386 }, none, 1), expected), "Extra card rejected");
            Check(!equal(Deck(new int[] { 3801, 4041 }, new int[] { 4386 }, none, 1), expected), "Missing card rejected");
            Check(!equal(Deck(new int[] { 3801, 3801, 4386 }, new int[] { 4041 }, none, 1), expected), "Main and Extra swap rejected");
            Check(!equal(Deck(new int[] { 3801, 3801, 4041 }, new int[] { 4386 }, new int[] { 4842 }, 1), expected), "Unexpected side card rejected");
            Check(!equal(null, expected) && !equal(expected, null), "Missing decks rejected");
            Check(equal(expected, Deck(new int[] { 3801, 3801, 4041 }, new int[] { 4386 }, none, 1)), "Checks leave trusted template unchanged");
            return 0;
        }
        catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
