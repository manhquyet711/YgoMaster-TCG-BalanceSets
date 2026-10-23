"""Apply era ban lists and full AI strength to the TCG solo campaign.

Usage: python apply_era_rules.py <Data folder> [--check]

- Era gates (2001-2006): every chapter gets the regulation of its
  "Progression Level" (level 01 -> "TCG 01_LOB ...", level 75 -> "TCG 75_ETCO ...").
  The level is read from the chapter description in ClientData/IDS/IDS_SOLO.txt.
- Challenger gates (2011-2015): the gate gets its named format.
- Every TCG campaign duel (gates 2001-2015) gets "cpu": 100.

Edits are textual so Solo.json keeps its comments and layout. Running it again
changes nothing. --check reports what would change without writing.
"""
import json
import re
import sys
from pathlib import Path

ERA_GATES = ["2001", "2002", "2003", "2004", "2005", "2006"]
CHALLENGER_FORMATS = {
    "2011": "TCG 75+ YGOMaster v1.60",
    "2012": "TCG 14+ 2005-04 Goat Format",
    "2013": "TCG 27+ 2008-01 Perfect Circle Format",
    "2014": "TCG 39+ 2010-03 Edison Format",
    "2015": "TCG 51+ 2014-04 HAT Format",
}
CPU_STRENGTH = 100


def loose_json(text):
    """Parse the campaign's JSON with // comments and trailing commas."""
    text = re.sub(r"(?m)^\s*//[^\n]*", "", text)
    text = re.sub(r"(?m)([,{\[])\s*//[^\n]*$", r"\1", text)
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def read_ids(path):
    entries, key = {}, None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("[IDS_"):
            key = line.strip("[] ")
            entries[key] = []
        elif key:
            entries[key].append(line)
    return {k: "\n".join(v) for k, v in entries.items()}


def main():
    data = Path(sys.argv[1])
    check = "--check" in sys.argv
    rules = loose_json((data / "RegulationInfo.json").read_text(encoding="utf-8-sig"))["rule_list"]
    names = set(rules.values())
    by_level = {}
    for name in rules.values():
        m = re.match(r"TCG (\d+)_\S+ ", name)
        if m:
            by_level[int(m.group(1))] = name
    for name in CHALLENGER_FORMATS.values():
        if name not in names:
            raise SystemExit("Missing regulation: " + name)

    solo_path = data / "Solo.json"
    raw = solo_path.read_bytes()
    text = raw.decode("utf-8-sig")
    bom = raw.startswith(b"\xef\xbb\xbf")
    solo = loose_json(text)["Master"]["Solo"]
    ids = read_ids(data / "ClientData/IDS/IDS_SOLO.txt")

    # Era chapters
    era_changes = 0
    for gate in ERA_GATES:
        for cid, row in solo["chapter"][gate].items():
            body = ids.get("IDS_SOLO.CHAPTER%s_EXPLANATION" % cid, "")
            m = re.search(r"Progression Level:\s*(\d+)", body)
            if not m or int(m.group(1)) not in by_level:
                raise SystemExit("No era format for chapter %s" % cid)
            name = by_level[int(m.group(1))]
            if row.get("regulation_name") == name:
                continue
            if "regulation_name" in row:
                raise SystemExit("Chapter %s already has regulation %r" % (cid, row["regulation_name"]))
            pattern = '"%s":{' % cid
            if text.count(pattern) != 1:
                raise SystemExit("Chapter %s found %d times in Solo.json" % (cid, text.count(pattern)))
            text = text.replace(pattern, pattern + '"regulation_name":%s,' % json.dumps(name))
            era_changes += 1

    # Challenger gates
    gate_changes = 0
    for gate, name in CHALLENGER_FORMATS.items():
        row = solo["gate"][gate]
        if row.get("regulation_name") == name:
            continue
        if "regulation_name" in row:
            raise SystemExit("Gate %s already has regulation %r" % (gate, row["regulation_name"]))
        pattern = '"%s":{"priority"' % gate
        if text.count(pattern) != 1:
            raise SystemExit("Gate %s found %d times in Solo.json" % (gate, text.count(pattern)))
        text = text.replace(pattern, '"%s":{"regulation_name":%s,"priority"' % (gate, json.dumps(name)))
        gate_changes += 1

    # Verify the edited Solo.json before writing it
    edited = loose_json(text)["Master"]["Solo"]
    for gate in ERA_GATES:
        for cid, row in edited["chapter"][gate].items():
            assert row.get("regulation_name") in names, cid
    for gate, name in CHALLENGER_FORMATS.items():
        assert edited["gate"][gate].get("regulation_name") == name, gate

    # AI strength in every TCG campaign duel
    duel_files = []
    for gate in ERA_GATES + list(CHALLENGER_FORMATS):
        for cid in solo["chapter"][gate]:
            p = data / "SoloDuels" / (cid + ".json")
            if p.exists():
                duel_files.append(p)
    cpu_changes = []
    for p in duel_files:
        with open(p, encoding="utf-8-sig", newline="") as fh:  # keep original line endings
            s = fh.read()
        duel = json.loads(s)["Duel"]
        if duel.get("cpu") == CPU_STRENGTH:
            continue
        if "cpu" in duel:
            raise SystemExit("%s already sets cpu=%r" % (p.name, duel["cpu"]))
        if not s.startswith('{"Duel":{'):
            raise SystemExit("Unexpected layout in " + p.name)
        new = '{"Duel":{"cpu":%d,' % CPU_STRENGTH + s[len('{"Duel":{'):]
        assert json.loads(new)["Duel"]["cpu"] == CPU_STRENGTH
        cpu_changes.append((p, new))

    print("era chapters: %d to set, challenger gates: %d to set, duels: %d of %d to set cpu=%d"
          % (era_changes, gate_changes, len(cpu_changes), len(duel_files), CPU_STRENGTH))
    if check:
        return
    if era_changes or gate_changes:
        solo_path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    for p, new in cpu_changes:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
    print("written")


if __name__ == "__main__":
    main()
