"""Group the Solo gates into modes: one parent gate per mode, with the mode's gates inside it.

Master Duel supports child gates (parent_gate), like the game's own gate 31 holding 22 and 30.
Gate IDs of the existing gates do not change, so progress and unlocks are kept.

Usage: python -I solo_modes.py <Data folder> [--check]
  Edits <Data>/Solo.json, ClientData/IDS/IDS_SOLO.txt and ClientData/SoloGateCards.txt in place,
  keeping their layout. Running it again changes nothing. --check only reports.

The Balanced Characters folder has no fixed children: the server moves the active deck set's
character gates into it at startup, so switching sets in the Settings Editor keeps the layout.
Duel Royale (2103) is added once its deck set is tested.
"""
import re
import sys
from pathlib import Path

# parent gate: (name, explanation, priority, category, thumbnail card id, child gate ids)
MODES = {
    2100: ("TCG Campaign",
           "Progressive campaign through the TCG eras, from Duel Monsters to VRAINS. Clear an era to open the next.",
           10, 1, 4007, [2001, 2002, 2003, 2004, 2005, 2006]),
    2101: ("Format Challenges",
           "Classic tournament formats with their ban lists: Goat, Perfect Circle, Edison, HAT and YgoMaster v1.60.",
           17, 2, 4041, [2012, 2013, 2014, 2015, 2011]),
    # Deck set folders: no fixed children. The server puts each set's character gates in its folder at
    # startup (Mode.json "sets"; GameServer.BalancedCharacters.cs, ApplyBalancedFolder) and removes a folder
    # whose set is not loaded.
    2102: ("Balanced Characters",
           "u/Rosehn's fixed character decks, balanced against each other. Pick a character, then beat every opponent.",
           20, 1, 4027, []),
    2104: ("Goat Era Duelists",
           "Eight duelists with fixed decks built from cards legal in the 2005 Goat format. Pick a character, then beat every opponent.",
           21, 1, 4370, []),
    2103: ("Duel Royale",
           "Konami's seven official Duel Royale decks, as printed: Dark Magician, Blue-Eyes, Gearfried, Lava Golem, "
           "A Legendary Ocean, Relinquished and Des Gardius. Pick one, then beat every other deck.",
           22, 1, 4088, []),
    # The original Master Duel gates (Tutorial, 48, and 31 with its own children 22 and 30), out of the way at the end.
    2109: ("Master Duel Basics",
           "The original Master Duel Solo gates: Tutorial and the basic story gates.",
           900, 2, 4064, [1, 48, 31]),
}


def gate_line_pattern(gate):
    return re.compile(r'(\n\s*"%d":\{[^\n]*?"parent_gate":)(\d+)' % gate)


def apply(data, check=False):
    data = Path(data)
    solo_path = data / "Solo.json"
    ids_path = data / "ClientData" / "IDS" / "IDS_SOLO.txt"
    cards_path = data / "ClientData" / "SoloGateCards.txt"
    solo = solo_path.read_text(encoding="utf-8-sig")
    ids = ids_path.read_text(encoding="utf-8-sig")
    cards = cards_path.read_text(encoding="utf-8-sig")
    changes = []
    for parent, (name, text, priority, category, card, children) in MODES.items():
        # parent gate entry, right after the opening of the gate table
        if not re.search(r'\n\s*"%d":\{' % parent, solo.split('"chapter":{')[0]):
            # goal: the last child's goal; 0 for a folder the server fills at startup
            clear = re.search(r'"%d":\{[^\n]*?"clear_chapter":(\d+)' % children[-1], solo).group(1) if children else "0"
            line = '\t\t"%d":{"priority":%d,"parent_gate":0,"unlock_id":0,"view_gate":0,"clear_chapter":%s,"category":%d},' % (
                parent, priority, clear, category)
            solo = solo.replace('\t"gate":{\n', '\t"gate":{\n\t\t//mode: %s\n%s\n' % (name, line), 1)
            changes.append("gate %d %s added" % (parent, name))
        for child in children:
            pattern = gate_line_pattern(child)
            m = pattern.search(solo)
            if not m:
                raise SystemExit("gate %d not found in Solo.json" % child)
            if m.group(2) != str(parent):
                solo = pattern.sub(lambda x: x.group(1) + str(parent), solo, count=1)
                changes.append("gate %d moved into %d" % (child, parent))
        key = "[IDS_SOLO.GATE%d]" % parent
        explanation_key = "[IDS_SOLO.GATE%d_EXPLANATION]]" % parent
        nl = "\r\n" if "\r\n" in ids else "\n"
        block = nl.join([key, name, explanation_key, text]) + nl
        old = re.search(re.escape(key) + r"\r?\n[^\r\n]*\r?\n" + re.escape(explanation_key) + r"\r?\n[^\r\n]*\r?\n", ids)
        if not old:
            ids = block + ids
            changes.append("text for gate %d added" % parent)
        elif old.group(0) != block:
            ids = ids[:old.start()] + block + ids[old.end():]
            changes.append("text for gate %d updated" % parent)
        if not re.search(r"(?m)^%d," % parent, cards):
            nl = "\r\n" if "\r\n" in cards else "\n"
            cards = cards.rstrip("\r\n") + nl + "%d,%d,0,0.2" % (parent, card) + nl
            changes.append("thumbnail for gate %d added" % parent)
    if not changes:
        print("already grouped: nothing to do")
        return
    print("\n".join(changes))
    if check:
        print("(check only: nothing written)")
        return
    solo_path.write_text(solo, encoding="utf-8")
    ids_path.write_text(ids, encoding="utf-8")
    cards_path.write_text(cards, encoding="utf-8")
    print("written to", data)


if __name__ == "__main__":
    apply(sys.argv[1], "--check" in sys.argv)
