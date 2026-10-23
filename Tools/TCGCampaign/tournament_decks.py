"""Give TCG campaign opponents real tournament decks (DM era, gate 2001).

Usage:
  python tournament_decks.py fetch <Data folder>   pick decks online and save them to
                                                   <Data>/TCGCampaign/TournamentDecks.json
  python tournament_decks.py apply <Data folder> [--check]
                                                   write the saved decks into the CPU side of each
                                                   duel and add a deck line to each chapter text

Sources:
- Real tournament decks from the time: yugiohtopdecks.com (Shonen Jump Championships,
  Nationals, Regionals) and Format Library's historical events (World Championship 2003,
  U.S. Nationals, SJCs).
- Retro tournaments on Format Library (today's players, same card pools), at most
  RETRO_PER_LEVEL normal duels per level.

Bosses (the duel that unlocks the next pack) use the hand-picked BOSS_PICKS. The other
duels of a level use real decks first (2nd-4th place preferred), then up to two retro decks;
any duel still without a legal deck keeps its original campaign deck. Every deck must be
legal in its chapter's own format (released cards and copy limits) and is used once.
Apply needs no network and is safe to run again.
"""
import collections
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "BalancedCharacters"))
from apply_era_rules import loose_json, read_ids  # noqa: E402

REVISION = "tournament-v2"
FL_API = "https://formatlibrary.com/api"
YTD = "https://yugiohtopdecks.com"
GATE = "2001"
RETRO_PER_LEVEL = 2
HISTORICAL_BEFORE = "2010"
MAX_RETRO_EVENTS_PER_FORMAT = 12
YTD_YEARS = (2002, 2003, 2004, 2005)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]

LEVEL_FORMATS = {1: "Yugi-Kaiba", 2: "Critter", 3: "Treasure", 4: "Imperial", 5: "Joey-Pegasus", 6: "Fiber",
                 7: "Yata", 8: "Scientist", 9: "Vampire", 10: "Chaos", 11: "Warrior", 12: "Goat", 13: "Goat", 14: "Goat"}

# boss chapter -> (Format Library event abbreviation, deck builder)
BOSS_PICKS = {
    "20010004": ("MBM11", "AlephYa2"),
    "20010010": ("DMD02", "dump truck"),
    "20010016": ("HUNT06", "lollo_8888"),
    "20010022": ("SPQR09", "mihawk"),
    "20010028": ("JOPE04", "itsgucci"),
    "20010034": ("DUMP13", "Arfio"),
    "20010040": ("WCS03", "Ng Yu Leung"),
    "20010046": ("SACK03", "WagaMuffin"),
    "20010052": ("DCD02", "OupsOfCow"),
    "20010058": ("USNC04", "Theerasak Poonsombat"),
    "20010064": ("SJCLV05", "Ian Wingrove"),
    "20010070": ("SJCCHA05", "Jae Kim"),
    "20010076": ("SJCNJ05", "Bryan Coronel"),
    "20010082": ("USNC05", "Max Suffridge"),
}


def http(url, cache={}):
    if url not in cache:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            cache[url] = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            cache[url] = None if error.code == 404 else _raise(error)
        time.sleep(0.3)
    return cache[url]


def _raise(error):
    raise error


def fl(path):
    return json.loads(http(FL_API + path))


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("&", "and"))


def placement_text(p):
    return {1: "1st", 2: "2nd", 3: "Top 4", 5: "Top 8"}.get(p, "Top %d" % p)


class Campaign:
    def __init__(self, data):
        self.data = data
        self.ydk = {}
        for line in (data / "YdkIds.txt").read_text(encoding="utf-8-sig").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit():
                self.ydk[int(parts[0])] = int(parts[1])
        self.solo = loose_json((data / "Solo.json").read_text(encoding="utf-8-sig"))["Master"]["Solo"]
        rules = loose_json((data / "RegulationInfo.json").read_text(encoding="utf-8-sig"))["rule_list"]
        self.regs = loose_json((data / "Regulation.json").read_text(encoding="utf-8-sig"))
        self.rid_by_name = {v: k for k, v in rules.items()}
        self.ids = read_ids(data / "ClientData/IDS/IDS_SOLO.txt")

    def level(self, chapter):
        body = self.ids.get("IDS_SOLO.CHAPTER%s_EXPLANATION" % chapter, "")
        return int(re.search(r"Progression Level:\s*(\d+)", body).group(1))

    def row(self, chapter):
        return self.solo["chapter"][chapter[:4]][chapter]

    def problem(self, entry, chapter):
        """None if the deck is legal for the chapter, else a reason."""
        main, extra = entry["main"], entry["extra"]
        if not 40 <= len(main) <= 60 or len(extra) > 15:
            return "deck size %d/%d" % (len(main), len(extra))
        available = self.regs[self.rid_by_name[self.row(chapter)["regulation_name"]]]["available"]
        limit = {c: 0 for c in available["a0"]}
        limit.update({c: 1 for c in available["a1"]})
        limit.update({c: 2 for c in available["a2"]})
        bad = [c for c, q in collections.Counter(main + extra).items() if q > limit.get(c, 3)]
        return "%d cards not legal" % len(bad) if bad else None


# ---------------------------------------------------------------- sources

def fl_entry(camp, event_info, top_deck, real):
    deck = fl("/decks/%d" % top_deck["id"])
    zone, codes = None, {"main": [], "extra": []}
    for line in deck["ydk"].splitlines():
        line = line.strip()
        if line in ("#main", "#extra", "!side"):
            zone = line.strip("#!")
        elif zone in codes and line.isdigit():
            codes[zone].append(int(line))
    main = [camp.ydk.get(c) for c in codes["main"]]
    extra = [camp.ydk.get(c) for c in codes["extra"]]
    if None in main or None in extra:
        return None
    return {"deckType": deck["deckTypeName"] or "Unknown", "builder": deck["builderName"],
            "event": event_info["name"], "eventDate": event_info["startedAt"][:10],
            "placement": top_deck["placement"], "real": real, "site": "formatlibrary.com",
            "source": "https://formatlibrary.com/decks/%d" % top_deck["id"], "main": main, "extra": extra[:15]}


def fl_events(fmt):
    events = fl("/events/gallery/" + fmt)["events"]
    hist = sorted([e for e in events if e["startedAt"] < HISTORICAL_BEFORE], key=lambda e: e["startedAt"])
    retro = sorted([e for e in events if e["startedAt"] >= HISTORICAL_BEFORE], key=lambda e: e["startedAt"],
                   reverse=True)[:MAX_RETRO_EVENTS_PER_FORMAT]
    return hist, retro


def ytd_decks(camp):
    """All 2002-2005 decks on yugiohtopdecks.com with every card resolved to a Master Duel id."""
    import content  # BalancedCharacters card name table
    by_name = {}
    for cid, name in sorted(content.card_table().items()):
        by_name.setdefault(norm_name(name), cid)
    out = []
    for year in YTD_YEARS:
        for month in MONTHS:
            page = http("%s/date/%s+%d" % (YTD, month, year))
            if not page or "Yugioh Top Decks" not in page:
                continue
            for row in re.findall(r"(?s)<tr.*?</tr>", page):
                deck_link = re.search(r'href="/deck/(\d+)"', row)
                if not deck_link:
                    continue

                def link(kind):
                    m = re.search(r'href="/%s/([^"]+)"' % kind, row)
                    return urllib.parse.unquote_plus(m.group(1)).replace("\xa0", " ").strip() if m else ""
                deck_id = deck_link.group(1)
                page_text = http("%s/deck/%s" % (YTD, deck_id))
                if not page_text:
                    continue
                body = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", page_text)
                lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", body)).replace("\xa0", " ").splitlines()
                         if l.strip()]
                title = re.search(r"<title>(.*?) by .*?\|", page_text)
                archetype = lines[lines.index("Main Archetype:") + 1] if "Main Archetype:" in lines else ""
                zone, cards, ok, i = None, {"main": [], "extra": []}, True, 0
                while i < len(lines):
                    l = lines[i]
                    if l.startswith("Main Deck"):
                        zone = "main"
                    elif l.startswith(("Extra Deck", "Fusion Deck")):
                        zone = "extra"
                    elif l.startswith("Side Deck"):
                        zone = None
                    elif zone and re.fullmatch(r"\d+x", l) and i + 1 < len(lines):
                        cid = by_name.get(norm_name(lines[i + 1]))
                        if cid is None:
                            ok = False
                        else:
                            cards[zone] += [cid] * int(l[:-1])
                        i += 1
                    i += 1
                placed = link("placed")
                place = 1 if placed.startswith("1st") else 2 if placed.startswith("2nd") else \
                    3 if placed.startswith("3rd") else 5 if placed.startswith("5th") else 9
                if ok:
                    out.append({"deckType": html.unescape(title.group(1)).strip() if title else archetype,
                                "archetype": archetype, "builder": link("duelist"), "event": link("tournament"),
                                "eventDate": "%s %d" % (month, year), "placement": place, "real": True,
                                "site": "yugiohtopdecks.com", "source": "%s/deck/%s" % (YTD, deck_id),
                                "main": cards["main"], "extra": cards["extra"][:15]})
    return out


# ---------------------------------------------------------------- fetch / apply

def fetch(data):
    camp = Campaign(data)
    chapters = sorted(camp.solo["chapter"][GATE], key=int)
    by_level = collections.defaultdict(list)
    for c in chapters:
        if (data / "SoloDuels" / (c + ".json")).exists():
            by_level[camp.level(c)].append(c)

    result, used = {}, set()

    def key(entry):  # the same deck listed on both sites counts once
        return (norm_name(entry["builder"]), entry["eventDate"][-4:] if entry["site"] == "yugiohtopdecks.com"
                else entry["eventDate"][:4])

    for chapter, (event, builder) in BOSS_PICKS.items():
        ev = fl("/events/" + event)
        td = min((d for d in ev["topDecks"] if d["builderName"] == builder), key=lambda d: d["placement"])
        entry = fl_entry(camp, ev["event"], td, ev["event"]["startedAt"] < HISTORICAL_BEFORE)
        entry["role"] = "boss"
        result[chapter] = entry
        used.add(key(entry))

    real_pool = ytd_decks(camp)
    retro_by_format = {}
    for fmt in dict.fromkeys(LEVEL_FORMATS.values()):
        hist, retro = fl_events(fmt)
        for e in hist:
            ev = fl("/events/" + e["abbreviation"])
            for td in ev["topDecks"]:
                entry = fl_entry(camp, ev["event"], td, True)
                if entry:
                    real_pool.append(entry)
        retro_by_format[fmt] = []
        for e in retro:
            ev = fl("/events/" + e["abbreviation"])
            for td in ev["topDecks"]:
                entry = fl_entry(camp, ev["event"], td, False)
                if entry:
                    retro_by_format[fmt].append(entry)
    # 2nd-4th place first, then winners, then lower placements
    order = lambda e: (0 if e["placement"] in (2, 3) else 1 if e["placement"] == 1 else 2, e["eventDate"])
    real_pool.sort(key=order)

    kept_original = []
    for level in sorted(by_level):
        normals = [c for c in by_level[level] if c not in BOSS_PICKS]
        retro = sorted(retro_by_format[LEVEL_FORMATS[level]], key=order)
        types_here, retro_here = collections.Counter(), 0
        for chapter in normals:
            chosen = None
            for prefer_new_type in (True, False):
                for pool in (real_pool, retro if retro_here < RETRO_PER_LEVEL else []):
                    for entry in pool:
                        kind = entry.get("archetype") or entry["deckType"]
                        if key(entry) in used or (prefer_new_type and types_here[kind]):
                            continue
                        if camp.problem(entry, chapter) is None:
                            chosen = entry
                            break
                    if chosen:
                        break
                if chosen:
                    break
            if not chosen:
                kept_original.append(chapter)
                continue
            chosen = dict(chosen, role="normal")
            used.add(key(chosen))
            types_here[chosen.get("archetype") or chosen["deckType"]] += 1
            retro_here += 0 if chosen["real"] else 1
            result[chapter] = chosen
        picked = [result[c] for c in normals if c in result]
        print("L%02d %-12s %d real, %d retro, %d original | %s" % (
            level, LEVEL_FORMATS[level], sum(e["real"] for e in picked), sum(not e["real"] for e in picked),
            len(normals) - len(picked), "; ".join("%s %s (%s, %s)" % (e["deckType"][:22], placement_text(e["placement"]),
                                                                       e["builder"][:16], e["event"][:28]) for e in picked)))

    out = data / "TCGCampaign" / "TournamentDecks.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schemaVersion": 2, "revision": REVISION, "keptOriginal": kept_original,
                               "decks": dict(sorted(result.items()))}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("wrote %s: %d decks, %d duels keep their original deck" % (out, len(result), len(kept_original)))


def apply(data, check):
    camp = Campaign(data)
    source = json.loads((data / "TCGCampaign" / "TournamentDecks.json").read_text(encoding="utf-8"))
    problems, changes = [], []
    for chapter, deck in source["decks"].items():
        problem = camp.problem(deck, chapter)
        if problem:
            problems.append("%s: %s" % (chapter, problem))
            continue
        path = data / "SoloDuels" / (chapter + ".json")
        with open(path, encoding="utf-8-sig", newline="") as fh:
            original = fh.read()
        body = original.rstrip("\r\n")
        d = json.loads(body)
        cpu = d["Duel"]["Deck"][1]
        cpu["Main"] = {"CardIds": deck["main"], "Rare": [1] * len(deck["main"])}
        cpu["Extra"] = {"CardIds": deck["extra"], "Rare": [1] * len(deck["extra"])}
        new = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        if new != body:
            changes.append((path, new + original[len(body):]))
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        raise SystemExit(1)

    ids_path = data / "ClientData/IDS/IDS_SOLO.txt"
    ids_bom = ids_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with open(ids_path, encoding="utf-8-sig", newline="") as fh:
        ids_text = fh.read()
    nl = "\r\n" if "\r\n" in ids_text else "\n"
    text_changes = 0
    for chapter, deck in source["decks"].items():
        key = "IDS_SOLO.CHAPTER%s_EXPLANATION" % chapter
        label = "Boss deck" if deck["role"] == "boss" else "Opponent deck"
        line = "%s: %s (%s, %s, %s)" % (label, deck["deckType"], deck["builder"], deck["event"],
                                       placement_text(deck["placement"]))
        # The game font lacks curly quotes (see SoloVisualNovel.cs); use plain ones.
        line = line.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        body = camp.ids.get(key)
        if body is None:
            problems.append("no description for " + chapter)
            continue
        kept = [l for l in body.split("\n") if not l.startswith(("Boss deck:", "Opponent deck:"))]
        old_block = "[%s]%s%s" % (key, nl, body.replace("\n", nl))
        new_block = "[%s]%s%s" % (key, nl, nl.join(kept + [line]))
        if old_block not in ids_text:
            problems.append("description layout not found for " + chapter)
            continue
        if new_block != old_block:
            ids_text = ids_text.replace(old_block, new_block, 1)
            text_changes += 1
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        raise SystemExit(1)
    roles = collections.Counter(d["role"] for d in source["decks"].values())
    real = sum(1 for d in source["decks"].values() if d["real"])
    print("decks: %d bosses, %d normal (%d real tournament decks, %d retro), %d duels keep their original deck"
          % (roles["boss"], roles["normal"], real, len(source["decks"]) - real, len(source.get("keptOriginal", []))))
    print("duel files to change: %d, chapter texts to change: %d" % (len(changes), text_changes))
    if check:
        return
    for path, content in changes:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
    if text_changes:
        with open(ids_path, "w", encoding="utf-8-sig" if ids_bom else "utf-8", newline="") as fh:
            fh.write(ids_text)
    print("written")


if __name__ == "__main__":
    mode, folder = sys.argv[1], Path(sys.argv[2])
    if mode == "fetch":
        fetch(folder)
    elif mode == "apply":
        apply(folder, "--check" in sys.argv)
    else:
        raise SystemExit(__doc__)
