"""Goat Era Duelists (source-v3): AI-designed balanced character decks, Goat-legal (April 2005).

Usage: python goat_set.py check     validate names, counts and Goat legality
       python goat_set.py write     write SourceDecks/source-v3/<id>.json (after check passes)
       python goat_set.py compare   build Testing/source-v3-compare (set + ALT_DECKS) for npc_balance --only

Design rules (shared by every deck):
- 40 main cards, every card in Master Duel and legal in "TCG 14_FET 2005-04 Goat Format".
- Equal staple share: Pot of Greed, Graceful Charity, one of Mystical Space Typhoon / Heavy Storm,
  and at most two premium removal traps (Mirror Force, Ring of Destruction, Torrential Tribute).
- No Goat tournament engines: no Black Luster Soldier / Chaos Sorcerer, no Scapegoat +
  Metamorphosis + Thousand-Eyes lock, no Sinister Serpent / Tsukuyomi loops, no Exodia.
- The rest are the character's own anime cards; aces get enough copies or support to show up.
Tune a deck by editing its list here, then run check, write, and the balance runner.
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "YgoMaster" / "Data"
MODE = DATA / "BalancedCharacters"
REVISION = "source-v3"
REGULATION = "TCG 14_FET 2005-04 Goat Format"

# (character id, display name, {main card: copies}, {extra card: copies})
DECKS = [
    ("goat_yugi", "Yugi Muto", {
        "Dark Magician": 3, "Dark Magician Girl": 1, "Buster Blader": 1,
        "Dark Magician of Chaos": 1, "Apprentice Magician": 2, "Summoned Skull": 2, "Big Shield Gardna": 1, "Kuriboh": 1, "Magician of Faith": 1,
        "Breaker the Magical Warrior": 1, "Skilled Dark Magician": 1, "Curse of Dragon": 1, "Gaia The Fierce Knight": 1,
        "Mystical Elf": 1, "Old Vindictive Magician": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Mystical Space Typhoon": 1, "Polymerization": 1,
        "Thousand Knives": 1, "Dark Magic Attack": 1, "Swords of Revealing Light": 1, "Mage Power": 1,
        "Premature Burial": 1, "Nobleman of Crossout": 1, "Card of Sanctity": 1, "Sangan": 1,
        "Mirror Force": 1, "Magic Cylinder": 1, "Shadow Spell": 1, "Magical Hats": 1, "Dust Tornado": 1,
        "Sakuretsu Armor": 1, "Waboku": 1, "Torrential Tribute": 1, "Call of the Haunted": 1,
    }, {"Dark Paladin": 1, "Gaia the Dragon Champion": 1}),
    ("goat_kaiba", "Seto Kaiba", {
        "Blue-Eyes White Dragon": 3, "Lord of D.": 1, "Rude Kaiser": 1, "Kaiser Glider": 1, "La Jinn the Mystical Genie of the Lamp": 1, "Hitotsu-Me Giant": 2, "X-Head Cannon": 1, "Y-Dragon Head": 1,
        "Z-Metal Tank": 1, "Spear Dragon": 1, "Battle Ox": 1, "Mystic Horseman": 1, "Luster Dragon": 1,
        "Saggi the Dark Clown": 1, "Blade Knight": 1, "Exiled Force": 1,
        "The Flute of Summoning Dragon": 2, "Polymerization": 1, "Pot of Greed": 1, "Graceful Charity": 1,
        "Mystical Space Typhoon": 1, "Burst Stream of Destruction": 1, "Enemy Controller": 1, "Soul Exchange": 1,
        "Premature Burial": 1,
        "Ring of Destruction": 1, "Interdimensional Matter Transporter": 1, "Negate Attack": 1, "Reinforcements": 1,
        "Ultimate Offering": 1, "Threatening Roar": 1, "Call of the Haunted": 1, "Shadow Spell": 1,
        "Dust Tornado": 1, "Sakuretsu Armor": 1, "Trap Hole": 1,
    }, {"Blue-Eyes Ultimate Dragon": 1, "XYZ-Dragon Cannon": 1}),
    ("goat_joey", "Joey Wheeler", {
        "Red-Eyes Black Dragon": 2, "Red-Eyes Black Metal Dragon": 1, "Gearfried the Iron Knight": 2,
        "Gearfried the Swordmaster": 1, "Jinzo": 1, "Little-Winguard": 1, "Flame Manipulator": 1, "Baby Dragon": 1,
        "Time Wizard": 1, "Axe Raider": 2, "Masaki the Legendary Swordsman": 1, "Goblin Attack Force": 2, "Marauding Captain": 1,
        "Command Knight": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Scapegoat": 1, "Polymerization": 1, "Graceful Dice": 1,
        "Shield & Sword": 1, "Release Restraint": 1, "Reinforcement of the Army": 1, "Heavy Storm": 1,
        "United We Stand": 1,
        "Skull Dice": 1, "Metalmorph": 1, "Lightning Blade": 1, "Big Bang Shot": 1, "Graverobber": 1,
        "Sakuretsu Armor": 1, "Dust Tornado": 1, "Torrential Tribute": 1, "Call of the Haunted": 1, "Waboku": 1,
        "Fairy Box": 1, "Mataza the Zapper": 1,
    }, {"Thousand Dragon": 1, "Flame Swordsman": 1}),
    ("goat_mai", "Mai Valentine", {
        "Harpie Lady 1": 1, "Harpie Lady 2": 1, "Harpie Lady 3": 1, "Harpie Lady Sisters": 3,
        "Harpie Lady": 2, "Harpie Girl": 1, "Harpie's Pet Dragon": 1, "Amazoness Tiger": 1, "Birdface": 2,
        "Amazoness Swords Woman": 1, "Amazoness Paladin": 1, "Sky Scout": 1, "Garuda the Wind Spirit": 1,
        "Skull Red Bird": 1, "Amazoness Fighter": 1,
        "Elegant Egotist": 2, "Harpies' Hunting Ground": 2, "Triangle Ecstasy Spark": 1, "Book of Moon": 1, "Amazoness Archer": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Mystical Space Typhoon": 1, "Rising Air Current": 1,
        "Mirror Wall": 1, "Soul Release": 1, "Phoenix Wing Wind Blast": 1, "Call of the Haunted": 1,
        "Shadow of Eyes": 1, "Sakuretsu Armor": 1, "Dust Tornado": 1, "Trap Hole": 1, "Mirror Force": 1,
        "Waboku": 1,
    }, {}),
    # Relinquished / Thousand-Eyes build (tested as Pegasus B): 48% vs the set; the Toon World build won 29%.
    ("goat_pegasus", "Maximillion Pegasus", {
        "Relinquished": 2, "Sonic Bird": 2, "Thousand-Eyes Idol": 2, "Illusionist Faceless Mage": 1,
        "Toon Summoned Skull": 1, "Toon Alligator": 1, "Mystic Tomato": 2, "Sangan": 1, "Magician of Faith": 1,
        "Spirit Reaper": 1, "D.D. Warrior Lady": 1, "Big Shield Gardna": 1, "Hane-Hane": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Mystical Space Typhoon": 1, "Black Illusion Ritual": 2,
        "Toon World": 1, "Polymerization": 1, "Mind Control": 1, "Swords of Revealing Light": 1,
        "Nobleman of Crossout": 1, "Premature Burial": 1, "Book of Moon": 1,
        "Magic Cylinder": 1, "Ring of Destruction": 1, "Torrential Tribute": 1, "Sakuretsu Armor": 1,
        "Dust Tornado": 1, "Call of the Haunted": 1, "Shadow Spell": 1, "Negate Attack": 1, "Trap Hole": 1,
        "Draining Shield": 1, "Waboku": 1,
    }, {"Thousand-Eyes Restrict": 1}),
    ("goat_bakura", "Yami Bakura", {
        "Dark Necrofear": 1, "Headless Knight": 1, "Earthbound Spirit": 2, "Souls of the Forgotten": 1,
        "The Gross Ghost of Fled Dreams": 1, "The Portrait's Secret": 1, "Whiptail Crow": 1, "Sangan": 1,
        "Morphing Jar": 1, "Spirit Reaper": 1, "Darklord Marie": 1, "Dark Ruler Ha Des": 1,
        "Ryu-Kishin Powered": 1, "Lesser Fiend": 1, "Invader of Darkness": 1,
        "Soul Release": 1, "Pot of Greed": 1, "Graceful Charity": 1, "Premature Burial": 1,
        "Nightmare Wheel": 1, "Mind Control": 1, "Mystical Space Typhoon": 1, "Spiritualism": 1, "Card Destruction": 1,
        "Book of Moon": 1,
        "Destiny Board": 1, 'Spirit Message "I"': 1, 'Spirit Message "N"': 1, 'Spirit Message "A"': 1,
        'Spirit Message "L"': 1, "Michizure": 1, "Dust Tornado": 1, "Call of the Haunted": 1,
        "Torrential Tribute": 1, "Magic Cylinder": 1, "Sakuretsu Armor": 1, "Deal of Phantom": 2, "Trap Hole": 1,
    }, {}),
    ("goat_marik", "Marik Ishtar", {
        "Lava Golem": 1, "Masked Sorcerer": 2, "Dark Jeroid": 1, "Revival Jam": 2, "Mystic Tomato": 1,
        "Bowganian": 2, "Slate Warrior": 1, "Newdoria": 1, "Fiend Comedian": 1, "Granadora": 1, "Sangan": 1,
        "Helpoemer": 1, "Exiled Force": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Mystical Space Typhoon": 1, "Mind Crush": 1,
        "Mind Control": 1, "Card Destruction": 1, "Premature Burial": 1, "Book of Moon": 1,
        "Monster Reincarnation": 1, "Nightmare Wheel": 1,
        "Drop Off": 2, "Jam Defender": 1, "Shadow Spell": 1, "Fake Trap": 1, "Magic Cylinder": 1, "Mirror Force": 1,
        "Dust Tornado": 1, "Call of the Haunted": 1, "Sakuretsu Armor": 1, "Trap Hole": 1, "Waboku": 1,
        "Negate Attack": 1, "Torrential Tribute": 1,
    }, {}),
    ("goat_ishizu", "Ishizu Ishtar", {
        "Mudora": 2, "Keldo": 2, "Kelbek": 2, "Agido": 2, "Zolga": 1, "Guardian Sphinx": 1, "Shining Angel": 2,
        "Airknight Parshath": 1, "Soul of Purity and Light": 1, "Asura Priest": 1, "Magician of Faith": 1,
        "Pot of Greed": 1, "Graceful Charity": 1, "Mystical Space Typhoon": 1, "Book of Moon": 1,
        "Premature Burial": 1, "Nobleman of Crossout": 1, "Card of Sanctity": 1,
        "Swords of Revealing Light": 1, "Reload": 1, "Card Destruction": 1,
        "Magic Drain": 1, "Mirror Force": 1, "Solemn Judgment": 1, "Sakuretsu Armor": 1,
        "Dust Tornado": 1, "Call of the Haunted": 1, "Waboku": 1, "Magic Cylinder": 1, "Trap Hole": 1,
        "Negate Attack": 1, "Torrential Tribute": 1, "Divine Wrath": 1, "Fairy Box": 1, "Draining Shield": 1,
    }, {}),
]
# Comparison-only decks: tested against the set (python goat_set.py compare), never shipped.
ALT_DECKS = []  # Pegasus B was promoted into DECKS (round 4)
COMPARE_DIR = HERE / "Testing" / "source-v3-compare"
FORBIDDEN_ENGINES = {"Black Luster Soldier - Envoy of the Beginning", "Chaos Sorcerer", "Metamorphosis",
                     "Thousand-Eyes Restrict_main", "Sinister Serpent", "Tsukuyomi", "Exodia the Forbidden One"}


def loose(text):
    text = re.sub(r"(?m)^\s*//[^\n]*", "", text)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def tables():
    sys.path.insert(0, str(HERE))
    import content
    names = content.card_table()
    by_name = collections.defaultdict(list)
    for cid, name in names.items():
        by_name[content.normalize(name)].append(cid)
    rules = loose((DATA / "RegulationInfo.json").read_text(encoding="utf-8-sig"))["rule_list"]
    regs = loose((DATA / "Regulation.json").read_text(encoding="utf-8-sig"))
    rid = next(k for k, v in rules.items() if v == REGULATION)
    av = regs[rid]["available"]
    limit = {c: 0 for c in av["a0"]}
    limit.update({c: 1 for c in av["a1"]})
    limit.update({c: 2 for c in av["a2"]})
    return content, by_name, limit


def check(verbose=True):
    content, by_name, limit = tables()
    problems = []
    for cid, name, main, extra in DECKS + ALT_DECKS:
        n_main, n_extra = sum(main.values()), sum(extra.values())
        if n_main != 40:
            problems.append("%s: %d main cards" % (cid, n_main))
        for zone, cards in (("main", main), ("extra", extra)):
            for card, q in cards.items():
                ids = [i for i in by_name.get(content.normalize(card), [])]
                legal = [i for i in ids if limit.get(i, 3) > 0]
                if not ids:
                    problems.append("%s: not in Master Duel: %s" % (cid, card))
                elif not legal:
                    problems.append("%s: not legal in Goat: %s" % (cid, card))
                elif q > limit.get(legal[0], 3):
                    problems.append("%s: %dx %s over the Goat limit (%d)" % (cid, q, card, limit.get(legal[0], 3)))
                if card in FORBIDDEN_ENGINES:
                    problems.append("%s: uses excluded engine card %s" % (cid, card))
        if verbose:
            print("%-12s %2d main %2d extra" % (cid, n_main, n_extra))
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        return False
    print("all %d decks valid (%d set + %d comparison): 40 cards, Goat-legal, in Master Duel" % (
        len(DECKS) + len(ALT_DECKS), len(DECKS), len(ALT_DECKS)))
    return True


def write():
    if not check(False):
        raise SystemExit(1)
    out = MODE / "SourceDecks" / REVISION
    out.mkdir(parents=True, exist_ok=True)
    for cid, name, main, extra in DECKS:
        doc = {"schemaVersion": 1, "characterId": cid, "displayName": name,
               "sourcePhoto": None, "verificationStatus": "designed",
               "design": "Goat Era Duelists: AI-designed balanced set (Tools/BalancedCharacters/goat_set.py)",
               "expectedMainCount": sum(main.values()), "expectedExtraCount": sum(extra.values()),
               "main": [{"name": k, "quantity": v, "status": "designed"} for k, v in main.items()],
               "extra": [{"name": k, "quantity": v, "status": "designed"} for k, v in extra.items()],
               "side": []}
        (out / (cid + ".json")).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote %d source decks to %s" % (len(DECKS), out))


def doc():
    """Write Docs/BalancedCharacters/Character_Deck_Lists_v3.md from DECKS."""
    content, by_name, limit = tables()
    lines = ["# Goat Era Duelists (source-v3)", "",
             "AI-designed balanced character decks, every card legal in the Goat format "
             "(April 2005 list, sets up to Flaming Eternity) and in Master Duel.",
             "Built and checked with `Tools/BalancedCharacters/goat_set.py`; balance is measured with "
             "`Tools/BalancedCharacters/npc_balance.py` (results in `Docs/BalancedCharacters/Balance/source-v3`).", ""]
    for cid, name, main, extra in DECKS:
        lines.append("## %s (%d cards%s)" % (name, sum(main.values()), ", Extra %d" % sum(extra.values()) if extra else ""))
        lines.append("")
        lines.append(", ".join("%dx %s" % (q, c) for c, q in main.items()))
        if extra:
            lines.append("")
            lines.append("Extra: " + ", ".join("%dx %s" % (q, c) for c, q in extra.items()))
        lines.append("")
    path = ROOT / "Docs" / "BalancedCharacters" / "Character_Deck_Lists_v3.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", path)


def compare():
    """Test folder: the compiled set decks plus the comparison decks, for
    npc_balance.py run --decks-dir Testing/source-v3-compare --only <comparison id>."""
    if not check(False):
        raise SystemExit(1)
    content, by_name, limit = tables()
    known = set(map(int, content.load_json(DATA / "CardList.json")))
    aliases = content.load_json(MODE / "Aliases.json") if (MODE / "Aliases.json").exists() else {}
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    for old in COMPARE_DIR.glob("*.json"):
        old.unlink()
    for path in (MODE / "Decks" / REVISION).glob("*.json"):
        (COMPARE_DIR / path.name).write_bytes(path.read_bytes())
    for cid, name, main, extra in ALT_DECKS:
        zones = {}
        for zone, cards in (("main", main), ("extra", extra)):
            rows = []
            for card, q in cards.items():
                alias = aliases.get(card) or {}
                if isinstance(alias, dict) and "masterDuelId" in alias:
                    ids = [alias["masterDuelId"]]
                else:
                    ids = [i for i in by_name.get(content.normalize(card), []) if i in known and limit.get(i, 3) > 0]
                if len(ids) != 1:
                    raise SystemExit("%s: %s matches %d cards; add it to Aliases.json" % (cid, card, len(ids)))
                rows.append({"cardId": ids[0], "quantity": q})
            zones[zone] = rows
        doc = {"schemaVersion": 1, "characterId": cid, "displayName": name, "revision": REVISION + "-compare",
               "main": zones["main"], "extra": zones["extra"], "side": []}
        (COMPARE_DIR / (cid + ".json")).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote %d decks to %s" % (len(list(COMPARE_DIR.glob("*.json"))), COMPARE_DIR))


if __name__ == "__main__":
    {"check": lambda: sys.exit(0 if check() else 1), "write": write, "doc": doc, "compare": compare}[sys.argv[1]]()
