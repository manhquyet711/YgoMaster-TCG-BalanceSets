"""Duel Royale (test only): Konami's 7 official pre-built decks, tested with the NPC balance runner.

Source: Konami OCG "Duel Royale Deck Set EX" (DR01, 2021) and "Duel Royale Deck Set EX ROUND2"
(DR02, 2022), card lists from Yugipedia ("Set Card Lists" pages), saved in Royale/decklists.json.
The decks are played as printed ("Royale rules": no Forbidden/Limited List).

Usage:
  python -I royale_set.py build      check every card is in Master Duel, write Testing/royale/*.json
  python -I npc_balance.py run --revision royale --decks-dir Testing/royale --games 20

Nothing here is added to the game. Shipping the set would mean a new revision through SourceDecks.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LISTS = HERE / "Royale" / "decklists.json"
OUT = HERE / "Testing" / "royale"

# deck name in decklists.json: (character id, display name)
DECKS = {
    "Dark Magician": ("royale_dark_magician", "Royale: Dark Magician (Yugi)"),
    "Blue-Eyes White Dragon": ("royale_blue_eyes", "Royale: Blue-Eyes (Kaiba)"),
    "Gearfried the Swordmaster": ("royale_gearfried", "Royale: Gearfried (Joey)"),
    "Lava Golem": ("royale_lava_golem", "Royale: Lava Golem (Marik)"),
    "A Legendary Ocean": ("royale_legendary_ocean", "Royale: Legendary Ocean (Mako)"),
    "Relinquished": ("royale_relinquished", "Royale: Relinquished (Pegasus)"),
    "Masked Beast Des Gardius": ("royale_des_gardius", "Royale: Des Gardius (Bakura)"),
}
EXTRA = {"Thousand-Eyes Restrict", "Sanwitch"}


def build():
    sys.path.insert(0, str(HERE))
    import content
    names = content.card_table()
    known = set(map(int, content.load_json(content.DATA / "CardList.json")))
    aliases = content.load_json(content.MODE / "Aliases.json")
    by_name = collections.defaultdict(list)
    for cid, name in names.items():
        if cid in known:
            by_name[content.normalize(name)].append(cid)
    lists = json.loads(LISTS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    problems = []
    for deck_name, cards in lists.items():
        cid, display = DECKS[deck_name]
        zones = {"main": [], "extra": []}
        for card, q in cards.items():
            alias = aliases.get(card)
            ids = [alias["masterDuelId"]] if isinstance(alias, dict) and "masterDuelId" in alias \
                else by_name.get(content.normalize(card), [])
            if len(ids) != 1:
                problems.append("%s: %s matches %d Master Duel cards" % (deck_name, card, len(ids)))
                continue
            if q > 3:
                problems.append("%s: %d copies of %s" % (deck_name, q, card))
            zones["extra" if card in EXTRA else "main"].append({"cardId": ids[0], "quantity": q})
        n_main = sum(r["quantity"] for r in zones["main"])
        if n_main != 40:
            problems.append("%s: %d main cards" % (deck_name, n_main))
        doc = {"schemaVersion": 1, "characterId": cid, "displayName": display, "revision": "royale-test",
               "source": "Konami OCG Duel Royale Deck Set (DR01/DR02), %s Deck" % deck_name,
               "main": zones["main"], "extra": zones["extra"], "side": []}
        (OUT / (cid + ".json")).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print("%-34s %d main, %d extra" % (display, n_main, sum(r["quantity"] for r in zones["extra"])))
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        raise SystemExit(1)
    print("wrote %d test decks to %s (game data unchanged)" % (len(lists), OUT))


if __name__ == "__main__":
    {"build": build}[sys.argv[1]]()
