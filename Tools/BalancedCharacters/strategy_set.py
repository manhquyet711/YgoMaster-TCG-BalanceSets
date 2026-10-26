"""Goat and Edison Format Strategies: real tournament decks, one per strategy, tuned for CPU balance.

Each pool is one format, so decks only meet decks from the same card pool and ban list:
  goat    April 2005 list (Data/Regulation.d/8000_Goat.json, the Format Challenges list)
  edison  March 2010 list (Data/Regulation.d/8001_Edison.json)

Deck lists come from Format Library (formatlibrary.com) tournament decks saved in
Tools/TCGCampaign/.cache. Main and Extra Deck are used as played; Side Decks are dropped.
Tuning changes are listed in TUNING and applied on top of the tournament list.

Usage:
  python -I strategy_set.py build [goat|edison]   check cards and legality, write Testing/strategy-<pool>/*.json
  python -I strategy_set.py list  [goat|edison]   print the deck lists
  python -I strategy_set.py write [goat|edison]   write the game source lists (SourceDecks/source-v5 Goat, source-v6 Edison)
  python -I npc_balance.py run --revision strategy-goat --decks-dir Testing/strategy-goat --games 20
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / "TCGCampaign" / ".cache"

POOLS = {
    "goat": {
        "regulation": "8000_Goat.json",
        # character id: (display name, Format Library deck id, why it is in the set)
        "decks": {
            "goat_control": ("Goat Control", 86362, "1st, PWCQ 92 (2026): the format's namesake control deck"),
            "chaos_turbo": ("Chaos Turbo", 86884, "1st, LCQ 3 (2026): fast Chaos monsters and draw power"),
            "warrior": ("Warrior Beatdown", 85971, "1st, GFC 2026: Warrior toolbox aggro"),
            "chaos_warrior": ("Chaos Warrior", 81492, "1st, PWCQ 89 (2026): two strategies, Chaos + Warrior"),
            "chaos_return": ("Chaos Return", 85245, "1st, TGFC 08 (2026): two strategies, Chaos + Return from the Different Dimension"),
            "panda_burn": ("Panda Burn", 86835, "1st, LCQ 2 (2026): burn behind stall cards"),
            "relinquished": ("Relinquished", 85996, "3rd, GFC 2026: ritual steal-and-equip"),
            "flip_control": ("Flip Control", 22590, "3rd, SWAG (2019): flip effects and card advantage"),
        },
    },
    "edison": {
        "regulation": "8001_Edison.json",
        "decks": {
            "blackwing": ("Blackwing", 83102, "1st, EWCQ (2026): swarm into Synchros"),
            "gladiator_beast": ("Gladiator Beast", 81930, "1st, PBR 56 (2026): tag-out beatdown with Contact Fusion"),
            "lightsworn": ("Lightsworn", 80898, "2nd, SESB 19 (2026): mill engine, Judgment Dragon"),
            "hero_frog": ("Hero Frog", 80909, "1st, SESB 19 (2026): two strategies, Elemental HERO + Frog monarch tributes"),
            "quickdraw_plant": ("Quickdraw Plant", 2981, "1st, SJC Edison (2010): the original Edison winner, Synchro combos"),
            "machina_gadget": ("Machina Gadget", 83179, "4th, EWCQ (2026): two strategies, Machina Fortress + Gadgets"),
            "vayu_turbo": ("Vayu Turbo", 85616, "1st, PBR 58 (2026): graveyard Synchros with Blackwing - Vayu"),
            "cat_control": ("Cat Control", 83230, "3rd, EWCQ (2026): Rescue Cat Synchro control"),
        },
    },
}

# Balance changes on top of the tournament lists: character id -> {card: +/- copies}.
TUNING = {
    "panda_burn": {"extra:Elemental HERO Flame Wingman": -1},  # not Goat-legal; unused by the deck
    # Round 2 (Goat): boost the weak decks, Panda Burn and Warrior unchanged. Each deck gets real
    # anti-lock tech (Dust Tornado for Gravity Bind / Level Limit / Nightmare Wheel, level 3-or-lower
    # attackers that get under Gravity Bind and Level Limit) in place of its weakest cards.
    # Round 3: Flip Control still 24% (no attackers); it gets monsters that remove face-down cards and beat.
    "flip_control": {"Time Seal": -1, "Skilled White Magician": -1, "Compulsory Evacuation Device": -1,
                     "Magical Merchant": -2, "Chaos Sorcerer": 2, "Dust Tornado": 2,
                     "Mask of Darkness": -2, "Tsukuyomi": -1, "Solemn Judgment": -1,
                     "Mystic Swordsman LV2": 2, "Exiled Force": 1, "Tribe-Infecting Virus": 1, "Zaborg the Thunder Monarch": 1},
    # Round 3: Chaos Turbo still 39%; Royal Decree (Goat Control's answer to burn and trap-heavy decks)
    # replaces Dust Tornado, and Zaborg adds a removal monster.
    "chaos_turbo": {"Trap Dustshoot": -2, "Card Destruction": -1, "Spirit Reaper": 1,
                    "Royal Decree": 2, "Dekoichi the Battlechanted Locomotive": -1, "Zaborg the Thunder Monarch": 1},
    "chaos_return": {"Roulette Barrel": -1, "Trap Dustshoot": -1, "Spirit Reaper": 1, "Dust Tornado": 1},
    # Round 3: Chaos Warrior 41%; it ran one Chaos monster only, now two Chaos Sorcerer and a third Warrior beater.
    "chaos_warrior": {"Upstart Goblin": -1, "Trap Dustshoot": -1, "Dust Tornado": 1, "Mystic Swordsman LV2": 1,
                      "Card Destruction": -1, "Injection Fairy Lily": -1, "Spirit Reaper": -1,
                      "Chaos Sorcerer": 2, "Blade Knight": 1},
    "relinquished": {"Upstart Goblin": -1, "Abyss Soldier": -1, "Dust Tornado": 2},
    # Round 2 (Edison): boost the weak decks, the top decks unchanged.
    # Vayu Turbo's graveyard tricks are hard for the CPU; it gets plain Blackwing beaters instead.
    "vayu_turbo": {"Deck Devastation Virus": -2, "Burial from a Different Dimension": -1,
                   "Return from the Different Dimension": -1, "Blackwing - Bora the Spear": 2,
                   "Blackwing - Kalut the Moon Shadow": 1, "Dimensional Prison": 1},
    "quickdraw_plant": {"Light and Darkness Dragon": -1, "Night Assailant": -1,
                        "Gorz the Emissary of Darkness": 1, "Dark Armed Dragon": 1},
    "hero_frog": {"Spiritual Water Art - Aoi": -1, "Dupe Frog": -1, "Bottomless Trap Hole": 1, "Dimensional Prison": 1},
}


def tables(regulation):
    sys.path.insert(0, str(HERE))
    import content
    names = content.card_table()
    known = set(map(int, content.load_json(content.DATA / "CardList.json")))
    by_name = collections.defaultdict(list)
    for cid, name in names.items():
        if cid in known:
            by_name[content.normalize(name)].append(cid)
    aliases = content.load_json(content.MODE / "Aliases.json") if (content.MODE / "Aliases.json").exists() else {}
    # Format Challenges ban lists (Data/Regulation.d): a0 forbidden, a1/a2 limited, a3 the legal card pool.
    banlist = content.load_json(content.DATA / "Regulation.d" / regulation)["banlist"]
    limit = {c: 0 for c in known}
    for key, n in (("a3", 3), ("a2", 2), ("a1", 1), ("a0", 0)):
        limit.update({c: n for c in banlist.get(key, [])})
    return content, by_name, aliases, limit, names


def source(deck_id):
    return json.loads((CACHE / ("formatlibrary_com_api_decks_%d.txt" % deck_id)).read_text(encoding="utf-8"))


def lists(pool):
    """character id -> (display name, note, {zone: Counter(card name)}) after TUNING."""
    out = {}
    for cid, (display, deck_id, note) in POOLS[pool]["decks"].items():
        d = source(deck_id)
        zones = {z: collections.Counter(c["name"] for c in d.get(z) or []) for z in ("main", "extra")}
        for card, delta in TUNING.get(cid, {}).items():
            zone = "extra" if card in zones["extra"] or card.startswith("extra:") else "main"
            card = card.replace("extra:", "")
            zones[zone][card] += delta
            if zones[zone][card] <= 0:
                del zones[zone][card]
        out[cid] = (display, note, zones)
    return out


def build(pool):
    content, by_name, aliases, limit, names = tables(POOLS[pool]["regulation"])
    folder = HERE / "Testing" / ("strategy-" + pool)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.json"):
        old.unlink()
    problems = []
    for cid, (display, note, zones) in lists(pool).items():
        doc = {"schemaVersion": 1, "characterId": cid, "displayName": display, "revision": "strategy-" + pool,
               "source": note, "main": [], "extra": [], "side": []}
        for zone, cards in zones.items():
            for card, q in cards.items():
                alias = aliases.get(card)
                ids = ([alias["masterDuelId"]] if isinstance(alias, dict) and "masterDuelId" in alias else []) \
                    + by_name.get(content.normalize(card), [])
                # Some cards have two Master Duel IDs (original and reprint); use the one the ban list knows.
                legal = [i for i in ids if limit.get(i, 0) > 0]
                ids = legal[:1] or ids[:1]
                if not ids:
                    problems.append("%s: not in Master Duel: %s" % (cid, card))
                    continue
                if q > limit.get(ids[0], 0):
                    problems.append("%s: %dx %s, %s allows %d" % (cid, q, card, pool, limit.get(ids[0], 0)))
                doc[zone].append({"cardId": ids[0], "quantity": q})
        n_main = sum(r["quantity"] for r in doc["main"])
        n_extra = sum(r["quantity"] for r in doc["extra"])
        if not 40 <= n_main <= 60 or n_extra > 15:
            problems.append("%s: %d main / %d extra" % (cid, n_main, n_extra))
        (folder / (cid + ".json")).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print("%-18s %2d main %2d extra  %s" % (display, n_main, n_extra, note))
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        raise SystemExit(1)
    print("wrote %d %s decks to %s (game data unchanged)" % (len(POOLS[pool]["decks"]), pool, folder))


# Gate thumbnail card and short map label per deck (content.py compile).
SHOWCASE = {
    "goat_control": ("Scapegoat", "Goat Control"), "chaos_turbo": ("Chaos Sorcerer", "Chaos Turbo"),
    "warrior": ("Blade Knight", "Warrior"), "chaos_warrior": ("Black Luster Soldier - Envoy of the Beginning", "Chaos Warrior"),
    "chaos_return": ("Return from the Different Dimension", "Chaos Return"), "panda_burn": ("Gyaku-Gire Panda", "Panda Burn"),
    "relinquished": ("Relinquished", "Relinquished"), "flip_control": ("Magician of Faith", "Flip Control"),
    "blackwing": ("Blackwing - Shura the Blue Flame", "Blackwing"), "gladiator_beast": ("Gladiator Beast Laquari", "Gladiator"),
    "lightsworn": ("Wulf, Lightsworn Beast", "Lightsworn"), "hero_frog": ("Swap Frog", "Hero Frog"),
    "quickdraw_plant": ("Quickdraw Synchron", "Quickdraw"), "machina_gadget": ("Machina Fortress", "Machina"),
    "vayu_turbo": ("Blackwing - Vayu the Emblem of Honor", "Vayu Turbo"), "cat_control": ("Rescue Cat", "Cat Control"),
}


def showcase():
    """{game character id: (signature card name, map label)} for both pools."""
    return {ID_PREFIX[pool] + cid: SHOWCASE[cid] for pool in POOLS for cid in POOLS[pool]["decks"]}


# In the game each pool is its own deck set and Solo folder (content.py SET_FOLDERS).
REVISIONS = {"goat": "source-v5", "edison": "source-v6"}
ID_PREFIX = {"goat": "goatfmt_", "edison": "edisonfmt_"}


def roster(pool):
    """(character id, display name, main count, extra count) rows for content.py."""
    return [(ID_PREFIX[pool] + cid, display, sum(zones["main"].values()), sum(zones["extra"].values()))
            for cid, (display, note, zones) in lists(pool).items()]


def write(pool):
    """Write the set's source lists (SourceDecks/<revision>) after the same checks as build."""
    build(pool)
    content, by_name, aliases, limit, names = tables(POOLS[pool]["regulation"])
    out = content.MODE / "SourceDecks" / REVISIONS[pool]
    out.mkdir(parents=True, exist_ok=True)
    for cid, (display, note, zones) in lists(pool).items():
        doc = {"schemaVersion": 1, "characterId": ID_PREFIX[pool] + cid, "displayName": display, "sourcePhoto": None,
               "verificationStatus": "designed",
               "design": "%s tournament deck from Format Library (%s), tuned with Tools/BalancedCharacters/strategy_set.py"
                         % (display, note),
               "expectedMainCount": sum(zones["main"].values()), "expectedExtraCount": sum(zones["extra"].values()),
               "main": [{"name": k, "quantity": v, "status": "designed"} for k, v in zones["main"].items()],
               "extra": [{"name": k, "quantity": v, "status": "designed"} for k, v in zones["extra"].items()],
               "side": []}
        (out / (doc["characterId"] + ".json")).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    print("wrote %d source decks to %s" % (len(POOLS[pool]["decks"]), out))


def show(pool):
    for cid, (display, note, zones) in lists(pool).items():
        print("## %s  (%s)" % (display, note))
        for zone, cards in zones.items():
            if cards:
                print("  %s: %s" % (zone, ", ".join("%dx %s" % (q, c) for c, q in sorted(cards.items(), key=lambda x: (-x[1], x[0])))))


if __name__ == "__main__":
    command = sys.argv[1]
    for pool in sys.argv[2:] or list(POOLS):
        {"build": build, "list": show, "write": write}[command](pool)
