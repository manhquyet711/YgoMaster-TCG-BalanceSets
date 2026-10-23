"""Make TCG campaign boss duels harder.

Usage: python apply_boss_rules.py <Data folder> [--check]

- Era bosses (the 2,000-gem duel of each level, gates 2001-2006): CPU at 12,000 LP and the
  CPU always goes first.
- Each era gate's final boss is loaner-only: the player must use that era's premade deck
  (the matching "Era ..." deck from TCGCampaign/EraReferenceDecks.json). Its reward moves
  from the own-deck slot (mydeck_set_id) to the loaner slot (set_id).
- Challenger gates 2012-2015 (every duel): CPU at 16,000 LP, 6-card opening hand, CPU first.
- Modern Challenger (2011): only its final duel gets 12,000 LP and CPU first.

Run apply_era_rules.py first. Running this again changes nothing. --check reports only.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_era_rules import ERA_GATES, loose_json, read_ids  # noqa: E402

BOSS_REWARD_SET = 3
CPU = 1  # DuelSettings.CpuIndex: FirstPlayer = 1 means the CPU goes first
# firstPlayerLocked tells the server to keep FirstPlayer instead of randomizing it
ERA_BOSS = {"life": [8000, 12000], "FirstPlayer": CPU, "firstPlayerLocked": True}
CHALLENGER = {"life": [8000, 16000], "hnum": [5, 6], "FirstPlayer": CPU, "firstPlayerLocked": True}
CHALLENGER_GATES = ["2012", "2013", "2014", "2015"]
MODERN_GATE = "2011"


def is_boss(row):
    return BOSS_REWARD_SET in (row.get("mydeck_set_id"), row.get("set_id"))


def main():
    data = Path(sys.argv[1])
    check = "--check" in sys.argv
    solo_path = data / "Solo.json"
    raw = solo_path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    solo = loose_json(text)["Master"]["Solo"]
    ids = read_ids(data / "ClientData/IDS/IDS_SOLO.txt")
    era_decks = json.loads((data / "TCGCampaign/EraReferenceDecks.json").read_text(encoding="utf-8"))["decks"]
    deck_by_level = {lvl: d for d in era_decks for lvl in d.get("levels", [])}

    duel_rules = {}   # chapter id -> settings to apply
    loaner = {}       # chapter id -> era deck
    for gate in ERA_GATES:
        bosses = []
        for cid, row in solo["chapter"][gate].items():
            if not is_boss(row):
                continue
            body = ids.get("IDS_SOLO.CHAPTER%s_EXPLANATION" % cid, "")
            level = int(re.search(r"Progression Level:\s*(\d+)", body).group(1))
            bosses.append((level, int(cid), cid))
            duel_rules[cid] = ERA_BOSS
        level, _, final = max(bosses)
        if level not in deck_by_level:
            raise SystemExit("No era deck for level %d (rebuild EraReferenceDecks.json)" % level)
        loaner[final] = deck_by_level[level]
    for gate in CHALLENGER_GATES:
        for cid in solo["chapter"][gate]:
            duel_rules[cid] = CHALLENGER
    duel_rules[str(solo["gate"][MODERN_GATE]["clear_chapter"])] = ERA_BOSS

    # Loaner-only chapters in Solo.json: reward moves from mydeck_set_id to set_id
    solo_changes = 0
    for cid in loaner:
        gate = cid[:4]
        row = solo["chapter"][gate][cid]
        if row.get("set_id") == BOSS_REWARD_SET and row.get("mydeck_set_id") == 0:
            continue
        m = re.search(r'"%s":\{[^}]*\}' % cid, text)
        if not m or text.count('"%s":{' % cid) != 1:
            raise SystemExit("Chapter %s not found once in Solo.json" % cid)
        entry = m.group(0)
        new = entry.replace('"set_id":0,', '"set_id":%d,' % BOSS_REWARD_SET, 1) \
                   .replace('"mydeck_set_id":%d,' % BOSS_REWARD_SET, '"mydeck_set_id":0,', 1)
        if new.count('"set_id":%d,' % BOSS_REWARD_SET) != 1 or '"mydeck_set_id":0,' not in new:
            raise SystemExit("Unexpected layout for chapter %s: %s" % (cid, entry))
        text = text.replace(entry, new)
        solo_changes += 1
    edited = loose_json(text)["Master"]["Solo"]
    for cid in loaner:
        row = edited["chapter"][cid[:4]][cid]
        assert row["set_id"] == BOSS_REWARD_SET and row["mydeck_set_id"] == 0, cid

    # Duel files
    duel_changes = []
    for cid, rules in sorted(duel_rules.items()):
        p = data / "SoloDuels" / (cid + ".json")
        with open(p, encoding="utf-8-sig", newline="") as fh:
            original = fh.read()
        body = original.rstrip("\r\n")
        tail = original[len(body):]
        d = json.loads(body)
        duel = d["Duel"]
        for key, value in rules.items():
            duel[key] = list(value) if isinstance(value, list) else value
        if cid in loaner:
            deck = loaner[cid]
            duel["Deck"][0] = {"Main": {"CardIds": list(deck["main"]), "Rare": [1] * len(deck["main"])},
                               "Extra": {"CardIds": list(deck["extra"]), "Rare": [1] * len(deck["extra"])},
                               "Side": {"CardIds": [], "Rare": []}}
        new = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        if new != body:
            duel_changes.append((p, new + tail))

    print("era bosses: %d, challenger duels: %d, modern final: 1, loaner-only finals: %s"
          % (sum(1 for r in duel_rules.values() if r is ERA_BOSS) - 1, sum(1 for r in duel_rules.values() if r is CHALLENGER),
             ", ".join("%s (%s)" % (c, loaner[c]["name"]) for c in sorted(loaner))))
    print("Solo.json chapters to change: %d, duel files to change: %d of %d" % (solo_changes, len(duel_changes), len(duel_rules)))
    if check:
        return
    if solo_changes:
        solo_path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    for p, content in duel_changes:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
    print("written")


if __name__ == "__main__":
    main()
