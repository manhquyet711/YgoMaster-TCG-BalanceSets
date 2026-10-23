"""Build one premade deck per TCG era format for the player's deck list.

Usage: python build_era_decks.py <Data folder>
Writes <Data folder>/TCGCampaign/EraReferenceDecks.json, read by the server
(GameServer.EraReferenceDecks.cs), which adds the decks to every player's deck list.

- Era levels that share a format name (e.g. levels 12-14 "Goat Format") share one deck.
- The deck starts from the boss duel (2000-gem chapter) of the first level in the group,
  trimmed to that level's regulation: forbidden cards removed, copies cut to the limit.
  Because later levels of a group keep the same ban list with a bigger card pool, the
  deck stays legal for the whole group.
- Challenger gates (2011-2015) get one deck each, from the gate's final duel.
- No cards are given; cards the player doesn't own show as missing in the deck editor.
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_era_rules import CHALLENGER_FORMATS, ERA_GATES, loose_json, read_ids  # noqa: E402

CHALLENGER_LABELS = {"2011": "Modern", "2012": "Goat", "2013": "Perfect Circle", "2014": "Edison", "2015": "HAT"}
BOSS_REWARD_SET = 3  # mydeck_set_id of the 2000-gem duels


def limits_for(regulation):
    available = regulation["available"]
    limit = {}
    for key, value in (("a0", 0), ("a1", 1), ("a2", 2)):
        for card in available.get(key, []):
            limit[card] = value
    return limit


def trim(cards, limit, removed, cap):
    """Keep card order, drop forbidden cards, cap copies at the regulation limit."""
    kept, counts = [], collections.Counter()
    for card in cards:
        allowed = min(limit.get(card, 3), cap)
        if counts[card] >= allowed:
            removed[card] += 1
            continue
        counts[card] += 1
        kept.append(card)
    return kept


def load_duel(data, chapter_id):
    p = data / "SoloDuels" / ("%s.json" % chapter_id)
    return json.loads(p.read_text(encoding="utf-8-sig"))["Duel"]


def main():
    data = Path(sys.argv[1])
    rules = loose_json((data / "RegulationInfo.json").read_text(encoding="utf-8-sig"))["rule_list"]
    regulations = loose_json((data / "Regulation.json").read_text(encoding="utf-8-sig"))
    ids_by_name = {name: int(rid) for rid, name in rules.items()}
    solo = loose_json((data / "Solo.json").read_text(encoding="utf-8-sig"))["Master"]["Solo"]
    text = read_ids(data / "ClientData/IDS/IDS_SOLO.txt")

    # level -> (regulation name, core set, boss chapter)
    levels = {}
    for gate in ERA_GATES:
        for cid, row in solo["chapter"][gate].items():
            body = text.get("IDS_SOLO.CHAPTER%s_EXPLANATION" % cid, "")
            level = int(re.search(r"Progression Level:\s*(\d+)", body).group(1))
            entry = levels.setdefault(level, {"regulation": row["regulation_name"], "boss": None, "gate": gate})
            # Loaner-only final bosses carry the reward in set_id instead of mydeck_set_id.
            if BOSS_REWARD_SET in (row.get("mydeck_set_id"), row.get("set_id")) and entry["boss"] is None:
                entry["boss"] = cid

    groups = collections.OrderedDict()
    for level in sorted(levels):
        name = levels[level]["regulation"]
        fmt = re.match(r"TCG \d+_\S+ \S+ (.+)$", name).group(1)  # e.g. "Goat Format"
        groups.setdefault(fmt, []).append(level)

    decks = []

    def add(key, deck_name, regulation_name, chapter, note, covered_levels=()):
        rid = ids_by_name[regulation_name]
        limit = limits_for(regulations[str(rid)])
        duel = load_duel(data, chapter)
        cpu = duel["Deck"][1]
        removed = collections.Counter()
        main = trim(cpu["Main"]["CardIds"], limit, removed, 3)
        extra = trim(cpu["Extra"]["CardIds"], limit, removed, 3)
        decks.append({"key": key, "name": deck_name, "regulationId": rid, "regulationName": regulation_name,
                      "sourceChapter": int(chapter), "sourceDuelist": duel["name"][1], "note": note,
                      "levels": list(covered_levels),
                      "main": main, "extra": extra, "removed": sum(removed.values())})

    for fmt, lvls in groups.items():
        first = lvls[0]
        boss = levels[first]["boss"]
        if boss is None:
            raise SystemExit("No boss duel for level %d" % first)
        span = "%02d" % first if len(lvls) == 1 else "%02d-%02d" % (first, lvls[-1])
        add("era-%02d" % first, "Era %s %s" % (span, fmt), levels[first]["regulation"], boss,
            "levels " + ", ".join(str(x) for x in lvls), lvls)

    for gate, regulation_name in CHALLENGER_FORMATS.items():
        final = str(solo["gate"][gate]["clear_chapter"])
        add("challenger-" + gate, "Challenger %s" % CHALLENGER_LABELS[gate], regulation_name, final,
            "gate %s final duel" % gate)

    out = data / "TCGCampaign"
    out.mkdir(exist_ok=True)
    payload = {"schemaVersion": 1, "revision": "era-decks-v1", "decks": decks}
    (out / "EraReferenceDecks.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    short = [d for d in decks if len(d["main"]) < 40]
    print("%d decks (%d era formats, %d challengers); %d cards trimmed in total; %d decks under 40 after trimming"
          % (len(decks), len(groups), len(CHALLENGER_FORMATS), sum(d["removed"] for d in decks), len(short)))
    for d in decks:
        print("  %-34s %-44s main %2d extra %2d trimmed %2d  from %s (%s)" % (
            d["name"], d["regulationName"][:44], len(d["main"]), len(d["extra"]), d["removed"],
            d["sourceChapter"], d["sourceDuelist"]))


if __name__ == "__main__":
    main()
