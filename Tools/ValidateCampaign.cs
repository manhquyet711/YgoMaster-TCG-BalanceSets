using System;
using System.Collections;
using System.IO;
using System.Reflection;

// Uses the compiled server's real parser and initialization, without opening network listeners.
class ValidateCampaign
{
    const BindingFlags Members = BindingFlags.Instance | BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
    static object Field(object instance, string name)
    {
        var field = instance.GetType().GetField(name, Members);
        if (field != null) return field.GetValue(instance);
        var property = instance.GetType().GetProperty(name, Members);
        if (property != null) return property.GetValue(instance, null);
        throw new Exception("Missing member: " + name);
    }
    static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
        Console.WriteLine("PASS " + message);
    }
    static int Main(string[] args)
    {
        try
        {
            string directory = Path.GetFullPath(args[0]);
            Environment.CurrentDirectory = directory;
            var assembly = Assembly.LoadFrom(Path.Combine(directory, "YgoMaster.exe"));
            var type = assembly.GetType("YgoMaster.GameServer", true);
            var server = Activator.CreateInstance(type, true);
            type.GetMethod("LoadSettings", Members).Invoke(server, null);
            var cards = (IDictionary)Field(server, "CardRare");
            var duels = (IDictionary)Field(server, "SoloDuels");
            var solo = (IDictionary)Field(server, "SoloData");
            var shop = Field(server, "Shop");
            var packs = (IDictionary)Field(shop, "PackShop");
            Check(cards.Count == 13997, "13997 catalog cards loaded");
            Check(duels.Count >= 678, "TCG campaign duels loaded: " + duels.Count);
            Check(packs.Count >= 250, "TCG shop packs loaded: " + packs.Count);
            Check(solo.Contains("chapter"), "Campaign chapter table loaded");
            int chapterCount = 0;
            foreach (DictionaryEntry gate in (IDictionary)solo["chapter"])
                chapterCount += ((IDictionary)gate.Value).Count;
            Check(chapterCount >= 678, "Campaign chapters loaded: " + chapterCount);
            Check((bool)Field(server, "ProgressiveCardList"), "Progressive card list retained");
            Check((bool)Field(server, "ProgressiveCardRarities"), "Progressive rarities retained");
            Check((int)Field(server, "MultiplayerPvpClientDoCommandUserOffset") == 15616, "Updated DoCommand offset");
            Check((int)Field(server, "MultiplayerPvpClientRunDialogUserOffset") == 15512, "Updated RunDialog offset");
            Check((int)cards[3433] == 3, "Custom TCG rarity retained");
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine(e);
            return 1;
        }
    }
}
