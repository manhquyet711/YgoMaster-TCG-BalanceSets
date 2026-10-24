"""Test-only tuning of the v2 deck set (original 2021 lists).

The original v2 decks in Data/BalancedCharacters/Decks/source-v2 are NOT changed and the game
never sees these. This script copies them, applies the swaps in CHANGES, and writes the result to
Tools/BalancedCharacters/Testing/source-v2-tuned/ for the NPC balance runner:

  python -I v2_tuning.py build
  python -I npc_balance.py run --revision source-v2-tuned --decks-dir Testing/source-v2-tuned --games 10

If a tuned set tests well, ship it as a new revision (source-v4) through the normal SourceDecks pipeline.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODE = ROOT / "YgoMaster" / "Data" / "BalancedCharacters"
SOURCE = MODE / "Decks" / "source-v2"
OUT = HERE / "Testing" / "source-v2-tuned"

# character id: (cards out, cards in), each {card name: copies}
CHANGES = {
    # 11%: half the deck is draw power with nothing to survive on. Keep Exodia, add stall the AI uses.
    "grandpa": ({"Emergency Provisions": 2, "Card Trader": 1, "Dark Factory of Mass Production": 1,
                 "Backup Soldier": 1, "Second Coin Toss": 1, "Ordeal of a Traveler": 1},
                {"Swords of Revealing Light": 1, "Big Shield Gardna": 2, "Spirit Reaper": 1,
                 "Nimble Momonga": 1, "Messenger of Peace": 1, "Marshmallon": 1}),
    # 24%: Toons stuck in hand without Toon World. Add searchers for it, cut the weakest monsters.
    "pegasus": ({"Dream Clown": 2, "Crass Clown": 2, "Dark Rabbit": 1, "Jigen Bakudan": 1, "Toon Defense": 1},
                {"Toon Table of Contents": 3, "Mind Control": 1, "Magic Cylinder": 1, "Toon Kingdom": 1,
                 "Shadow Spell": 1}),
    # 66%: generic removal on top of a solid beatdown. Swap three removal cards for Rex's own support.
    "rex": ({"Dark Hole": 1, "Mind Control": 1, "De-Spell": 1},
            {"Little D": 1, "Sword Arm of Dragon": 1, "Miracle Jurassic Egg": 1}),
    # 63%: three Necrovalley lock out the AI's graveyard plays. One fewer field and no Dark Hole.
    "gravekeepers": ({"Necrovalley": 1, "Dark Hole": 1},
                     {"Gravekeeper's Vassal": 1, "Gravekeeper's Servant": 1}),
    # 61%: slightly strong; trade one removal for a weaker anime card.
    "joey": ({"Kunai with Chain": 1}, {"Little-Winguard": 1}),
}


def tables():
    sys.path.insert(0, str(HERE))
    import content
    names = content.card_table()
    known = set(map(int, content.load_json(content.DATA / "CardList.json")))
    by_name = collections.defaultdict(list)
    for cid, name in names.items():
        if cid in known:
            by_name[content.normalize(name)].append(cid)
    return content, names, by_name


def build():
    content, names, by_name = tables()
    OUT.mkdir(parents=True, exist_ok=True)
    problems = []
    for path in sorted(SOURCE.glob("*.json")):
        deck = json.loads(path.read_text(encoding="utf-8"))
        cid = deck["characterId"]
        main = collections.Counter()
        for row in deck["main"]:
            main[row["cardId"]] += row["quantity"]
        out, add = CHANGES.get(cid, ({}, {}))
        for card, q in out.items():
            ids = [i for i in main if content.normalize(names.get(i, "")) == content.normalize(card)]
            have = sum(main[i] for i in ids)
            if have < q:
                problems.append("%s: has %d %s, cannot remove %d" % (cid, have, card, q))
                continue
            for i in ids:
                take = min(q, main[i]); main[i] -= take; q -= take
                if not main[i]:
                    del main[i]
        for card, q in add.items():
            ids = by_name.get(content.normalize(card), [])
            if len(ids) != 1:
                problems.append("%s: %s matches %d Master Duel cards" % (cid, card, len(ids)))
                continue
            main[ids[0]] += q
        total = sum(main.values())
        if total != 40:
            problems.append("%s: %d main cards" % (cid, total))
        over = [names.get(i, i) for i, q in main.items() if q > 3]
        if over:
            problems.append("%s: more than 3 of %s" % (cid, ", ".join(over)))
        tuned = dict(deck, revision="source-v2-tuned", main=[{"cardId": i, "quantity": q} for i, q in main.items()])
        (OUT / path.name).write_text(json.dumps(tuned, indent=2) + "\n", encoding="utf-8")
        if cid in CHANGES:
            print("%-13s -%d +%d -> %d cards" % (cid, sum(out.values()), sum(add.values()), total))
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        raise SystemExit(1)
    print("wrote %d test decks to %s (game data unchanged)" % (len(list(OUT.glob("*.json"))), OUT))


if __name__ == "__main__":
    {"build": build}[sys.argv[1]]()
