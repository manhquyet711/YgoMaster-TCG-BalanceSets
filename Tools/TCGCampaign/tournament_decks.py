"""Give TCG campaign opponents real tournament decks.

Usage:
  python tournament_decks.py fetch <Data folder> [--cache DIR]
        pick decks online and save them to <Data>/TCGCampaign/TournamentDecks.json
        (keeps every pick already in that file; downloads are cached in DIR,
        default Tools/TCGCampaign/.cache)
  python tournament_decks.py apply <Data folder> [--check]
        write the saved decks into the CPU side of each duel and add a deck line
        to each chapter description (no network needed, safe to run again)

Covers the six era gates (2001-2006, 75 progression levels) and the Goat, Perfect Circle,
Edison and HAT challenger gates (2012-2015). The Modern Challenger post-game (2011) is left as is.

Sources:
- Real decks from the time: Yugioh Top Decks (yugiohtopdecks.com) and Format Library's
  historical events (World Championship, Nationals, Shonen Jump / YCS events).
- Retro decks: Format Library's retro-format tournaments (today's players, same card pools).

Picking, per chapter:
- Bosses (the duel that unlocks the next pack): real event winners first, then real 2nd/Top 4,
  then retro winners. DM bosses use the hand-picked DM_BOSS_PICKS.
- Normal duels: real 2nd-4th place first, then other real decks, then retro decks.
- Real decks must come from around the level's own period (see window()); every deck must be
  legal in the chapter's format (released cards and copy limits), have 40-60 main cards with
  every card in Master Duel, and is used only once. A duel with no legal deck keeps its
  original campaign deck.
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

REVISION = "tournament-v3"
FL_API = "https://formatlibrary.com/api"
YTD = "https://yugiohtopdecks.com"
ERA_GATES = ["2001", "2002", "2003", "2004", "2005", "2006"]
CHALLENGER_GATES = {"2012": ["Goat", "Cyber"], "2013": ["Perfect Circle", "DAD Return"],
                    "2014": ["Edison", "Frog"], "2015": ["HAT", "Shaddoll"]}
BOSS_REWARD_SET = 3
REAL_BEFORE = "2020"          # Format Library events before the retro scene are historical
MAX_RETRO_EVENTS_PER_FORMAT = 10
YTD_YEARS = range(2002, 2021)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]

# DM bosses were hand-picked: chapter -> (Format Library event, builder)
DM_BOSS_PICKS = {
    "20010004": ("MBM11", "AlephYa2"), "20010010": ("DMD02", "dump truck"),
    "20010016": ("HUNT06", "lollo_8888"), "20010022": ("SPQR09", "mihawk"),
    "20010028": ("JOPE04", "itsgucci"), "20010034": ("DUMP13", "Arfio"),
    "20010040": ("WCS03", "Ng Yu Leung"), "20010046": ("SACK03", "WagaMuffin"),
    "20010052": ("DCD02", "OupsOfCow"), "20010058": ("USNC04", "Theerasak Poonsombat"),
    "20010064": ("SJCLV05", "Ian Wingrove"), "20010070": ("SJCCHA05", "Jae Kim"),
    "20010076": ("SJCNJ05", "Bryan Coronel"), "20010082": ("USNC05", "Max Suffridge"),
}

CACHE = HERE / ".cache"


def http(url):
    f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url.split("://", 1)[1])[:180] + ".txt")
    if f.exists():
        t = f.read_text(encoding="utf-8")
        return None if t == "\0404" else t
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as error:
            if error.code == 404:
                t = None
                break
            if attempt == 2:
                print("  skipped (HTTP %d): %s" % (error.code, url), flush=True)
                return None  # server error: skip this page for now, not cached
            time.sleep(5)
        except Exception as error:
            if attempt == 2:
                print("  skipped (%s): %s" % (type(error).__name__, url), flush=True)
                return None
            time.sleep(5)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text("\0404" if t is None else t, encoding="utf-8")
    time.sleep(0.25)
    return t


def fl(path):
    t = http(FL_API + path)
    return json.loads(t) if t else None


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("&", "and"))


def placement_text(p):
    if p <= 2:
        return {1: "1st", 2: "2nd"}[max(p, 1)]
    for top in (4, 8, 16, 32, 64):
        if p <= top:
            return "Top %d" % top
    return "Top 128"


def month_index(year, month):
    return year * 12 + month - 1


def event_text(deck):
    """'SJC Pomona, April 2005': event name without a repeated year, then its month and year."""
    date = str(deck.get("eventDate", ""))
    m = re.match(r"(\d{4})-(\d{2})", date)
    when = "%s %s" % (MONTHS[int(m.group(2)) - 1], m.group(1)) if m else date
    year = re.search(r"\d{4}", when)
    name = deck["event"].strip().rstrip(",;:-").strip()
    if year:
        name = re.sub(r"(^%s\s+|\s+%s$)" % (year.group(0), year.group(0)), "", name).strip()
    return "%s, %s" % (name, when) if when else name


def font_safe(text):
    """Keep ASCII, Latin-1 accents and CJK; simplify other accented letters (c-caron -> c)."""
    import unicodedata
    out = []
    for ch in text:
        if ord(ch) < 256 or 0x3000 <= ord(ch) <= 0x9FFF:
            out.append(ch)
        else:
            base = unicodedata.normalize("NFKD", ch)[0]
            out.append(base if ord(base) < 128 else "")
    return "".join(out)


def deck_line(deck):
    label = "Boss deck" if deck["role"] == "boss" else "Opponent deck"
    deck_type = deck["deckType"] if deck.get("deckType") and deck["deckType"] not in ("Unknown", "Other") else "Tournament deck"
    line = "%s: %s (%s, %s, %s)" % (label, deck_type, deck["builder"], event_text(deck), placement_text(deck["placement"]))
    # The game font lacks curly quotes (see SoloVisualNovel.cs); use plain ones.
    line = line.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return font_safe(line)


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
        self._limits = {}

    def level(self, chapter):
        body = self.ids.get("IDS_SOLO.CHAPTER%s_EXPLANATION" % chapter, "")
        m = re.search(r"Progression Level:\s*(\d+)", body)
        return int(m.group(1)) if m else None

    def row(self, chapter):
        return self.solo["chapter"][chapter[:4]][chapter]

    def regulation_name(self, chapter):
        return self.row(chapter).get("regulation_name") or self.solo["gate"][chapter[:4]].get("regulation_name")

    def regulation_month(self, chapter):
        m = re.search(r"(\d{4})[-_](\d{2})", self.regulation_name(chapter))
        return month_index(int(m.group(1)), int(m.group(2)))

    def limits(self, chapter):
        name = self.regulation_name(chapter)
        if name not in self._limits:
            available = self.regs[self.rid_by_name[name]]["available"]
            limit = {c: 0 for c in available["a0"]}
            limit.update({c: 1 for c in available["a1"]})
            limit.update({c: 2 for c in available["a2"]})
            self._limits[name] = limit
        return self._limits[name]

    def problem(self, entry, chapter):
        """None if the deck is legal for the chapter, else a reason."""
        main, extra = entry["main"], entry["extra"]
        if not 40 <= len(main) <= 60 or len(extra) > 15:
            return "deck size %d/%d" % (len(main), len(extra))
        limit = self.limits(chapter)
        bad = [c for c, q in collections.Counter(main + extra).items() if q > limit.get(c, 3)]
        return "%d cards not legal" % len(bad) if bad else None


# ---------------------------------------------------------------- candidate decks (cards load lazily)

class Candidate:
    def __init__(self, meta, loader):
        self.meta, self._loader, self._cards = meta, loader, False

    def cards(self):
        if self._cards is False:
            self._cards = self._loader()
        return self._cards

    def entry(self):
        cards = self.cards()
        return dict(self.meta, main=cards[0], extra=cards[1][:15]) if cards else None


def fl_loader(camp, deck_id):
    def load():
        deck = fl("/decks/%d" % deck_id)
        if not deck or not deck.get("ydk"):
            return None
        zone, codes = None, {"main": [], "extra": []}
        for line in deck["ydk"].splitlines():
            line = line.strip()
            if line in ("#main", "#extra", "!side"):
                zone = line.strip("#!")
            elif zone in codes and line.isdigit():
                codes[zone].append(int(line))
        main = [camp.ydk.get(c) for c in codes["main"]]
        extra = [camp.ydk.get(c) for c in codes["extra"]]
        return None if None in main or None in extra else (main, extra)
    return load


def fl_candidates(camp, formats):
    """Top decks of all Format Library events of the given formats."""
    out = []
    for fmt in formats:
        gallery = fl("/events/gallery/" + urllib.parse.quote(fmt))
        if not gallery:
            continue
        events = gallery["events"]
        real = [e for e in events if e["startedAt"] < REAL_BEFORE]
        retro = sorted([e for e in events if e["startedAt"] >= REAL_BEFORE], key=lambda e: e["startedAt"],
                       reverse=True)[:MAX_RETRO_EVENTS_PER_FORMAT]
        for e in real + retro:
            ev = fl("/events/" + urllib.parse.quote(e["abbreviation"]))
            if not ev:
                continue
            info = ev["event"]
            for td in ev.get("topDecks", []):
                y, m = int(info["startedAt"][:4]), int(info["startedAt"][5:7])
                meta = {"deckType": td.get("deckTypeName") or "Unknown", "builder": td.get("builderName") or "Unknown",
                        "event": info["name"], "eventDate": info["startedAt"][:10], "month": month_index(y, m),
                        "placement": td["placement"], "real": info["startedAt"] < REAL_BEFORE,
                        "site": "formatlibrary.com", "source": "https://formatlibrary.com/decks/%d" % td["id"],
                        "format": fmt}
                out.append(Candidate(meta, fl_loader(camp, td["id"])))
    return out


def ytd_candidates(camp):
    import content  # BalancedCharacters card name table
    by_name = {}
    for cid, name in sorted(content.card_table().items()):
        by_name.setdefault(norm_name(name), cid)
    out = []
    for year in YTD_YEARS:
        for mi, month in enumerate(MONTHS, 1):
            page = http("%s/date/%s+%d" % (YTD, month, year))
            if not page or "Yugioh Top Decks" not in page:
                continue
            for row in re.findall(r"(?s)<tr.*?</tr>", page):
                deck_link = re.search(r'href="/deck/(\d+)"', row)
                if not deck_link:
                    continue

                def link(kind, row=row):
                    m = re.search(r'href="/%s/([^"]+)"' % kind, row)
                    return urllib.parse.unquote_plus(m.group(1)).replace("\xa0", " ").strip() if m else ""
                placed = link("placed")
                place = 1 if placed.startswith("1st") else 2 if placed.startswith("2nd") else \
                    3 if placed.startswith("3rd") else 5 if placed.startswith("5th") else 9
                deck_id = deck_link.group(1)
                name = re.search(r'href="/deck/\d+"[^>]*>([^<]*)<', row)
                meta = {"deckType": html.unescape(name.group(1)).strip() if name else "Unknown",
                        "builder": link("duelist") or "Unknown", "event": link("tournament") or "Unknown",
                        "eventDate": "%s %d" % (month, year), "month": month_index(year, mi), "placement": place,
                        "real": True, "site": "yugiohtopdecks.com", "source": "%s/deck/%s" % (YTD, deck_id)}

                def load(deck_id=deck_id):
                    page_text = http("%s/deck/%s" % (YTD, deck_id))
                    if not page_text:
                        return None
                    body = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", page_text)
                    lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", body)).replace("\xa0", " ").splitlines()
                             if l.strip()]
                    zone, cards, i = None, {"main": [], "extra": []}, 0
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
                                return None
                            cards[zone] += [cid] * int(l[:-1])
                            i += 1
                        i += 1
                    return cards["main"], cards["extra"]
                out.append(Candidate(meta, load))
    return out


# ---------------------------------------------------------------- fetch

def fetch(data):
    camp = Campaign(data)
    out_path = data / "TCGCampaign" / "TournamentDecks.json"
    previous = json.loads(out_path.read_text(encoding="utf-8"))["decks"] if out_path.exists() else {}

    formats = sorted([f for f in fl("/formats") if (f.get("category") or "").upper() == "TCG" and f.get("date")],
                     key=lambda f: f["date"])
    fmt_month = {f["name"]: month_index(int(f["date"][:4]), int(f["date"][5:7])) for f in formats}

    # Levels: chapters, period start (regulation month) and next level's start
    level_chapters = collections.defaultdict(list)
    for gate in ERA_GATES:
        for c in camp.solo["chapter"][gate]:
            if (data / "SoloDuels" / (c + ".json")).exists():
                level_chapters[camp.level(c)].append(c)
    level_start = {lvl: camp.regulation_month(chs[0]) for lvl, chs in level_chapters.items()}
    groups = []  # (label, chapters, window start, window end, Format Library formats)
    for lvl in sorted(level_chapters):
        start = level_start[lvl]
        end = level_start.get(lvl + 1, start + 6)
        # real decks: from the level's release until the next level is out (+3 months of events)
        win = (start - 1, max(end, start + 2) + 3)
        fmts = [f for f, m in fmt_month.items() if win[0] - 6 <= m <= win[1] + 3]
        groups.append(("L%02d" % lvl, sorted(level_chapters[lvl], key=int), win, fmts))
    for gate, fmts in CHALLENGER_GATES.items():
        chs = sorted(c for c in camp.solo["chapter"][gate] if (data / "SoloDuels" / (c + ".json")).exists())
        groups.append(("Challenger " + fmts[0], chs, None, fmts))

    def key(meta):  # the same deck listed on both sites counts once
        return (norm_name(meta["builder"]), str(meta["eventDate"])[-4:] if meta["site"] == "yugiohtopdecks.com"
                else str(meta["eventDate"])[:4], norm_name(meta["event"])[:6] if meta["builder"] == "Unknown" else "")

    result, used = {}, set()
    for chapter, entry in previous.items():   # keep earlier picks
        result[chapter] = entry
        used.add(key(entry))

    print("loading Yugioh Top Decks index ...", flush=True)
    ytd = ytd_candidates(camp)
    print("  %d decks listed" % len(ytd), flush=True)
    fl_cache = {}

    def fl_for(fmts):
        out = []
        for f in fmts:
            if f not in fl_cache:
                fl_cache[f] = fl_candidates(camp, [f])
            out += fl_cache[f]
        return out

    # Variety: how often each deck type is already used in each gate
    gate_types = collections.defaultdict(collections.Counter)
    for chapter, entry in result.items():
        gate_types[chapter[:4]][norm_name(entry["deckType"])] += 1

    kept_original = []
    for label, chapters, win, fmts in groups:
        pool = fl_for(fmts)
        fl_formats = set(fmts)
        if win:
            real = [c for c in pool + ytd if c.meta["real"] and win[0] <= c.meta["month"] <= win[1]]
        else:   # challengers: real decks from the format's own events
            real = [c for c in pool if c.meta["real"] and c.meta["format"] in fl_formats]
        retro = [c for c in pool if not c.meta["real"]]
        mid = (win[0] + win[1]) / 2 if win else 0
        normal_rank = lambda c: (0 if c.meta["placement"] in (2, 3) else 1 if c.meta["placement"] == 1 else 2,
                                 abs(c.meta["month"] - mid) if win else 0)
        boss_rank = lambda c: (c.meta["placement"], abs(c.meta["month"] - mid) if win else 0)
        types_here = collections.Counter(result[c]["deckType"] for c in chapters if c in result)
        filled = []
        for chapter in chapters:
            if chapter in result:
                continue
            row = camp.row(chapter)
            is_boss = BOSS_REWARD_SET in (row.get("mydeck_set_id"), row.get("set_id")) and chapter[:4] in ERA_GATES
            if chapter in DM_BOSS_PICKS:
                event, builder = DM_BOSS_PICKS[chapter]
                ev = fl("/events/" + event)
                td = min((d for d in ev["topDecks"] if d["builderName"] == builder), key=lambda d: d["placement"])
                pools = [[c for c in pool if c.meta["source"].endswith("/%d" % td["id"])]]
            else:
                rank = boss_rank if is_boss else normal_rank
                seen = gate_types[chapter[:4]]
                # normal duels: strategies used least in this gate come first, then placement
                varied = (lambda c: (seen[norm_name(c.meta["deckType"])],) + rank(c)) if not is_boss else rank
                pools = [sorted(real, key=varied), sorted(retro, key=varied)]
            chosen = None
            for prefer_new_type in (True, False):
                for candidates in pools:
                    for cand in candidates:
                        if key(cand.meta) in used or (prefer_new_type and types_here[cand.meta["deckType"]]):
                            continue
                        entry = cand.entry()
                        if entry and camp.problem(entry, chapter) is None:
                            chosen = entry
                            break
                    if chosen:
                        break
                if chosen:
                    break
            if not chosen:
                kept_original.append(chapter)
                continue
            chosen["role"] = "boss" if is_boss else "normal"
            chosen.pop("month", None)
            used.add(key(chosen))
            types_here[chosen["deckType"]] += 1
            gate_types[chapter[:4]][norm_name(chosen["deckType"])] += 1
            result[chapter] = chosen
            filled.append(chosen)
        here = [result[c] for c in chapters if c in result]
        print("%-22s %2d duels: %2d real, %2d retro, %2d original (new: %d)" % (
            label, len(chapters), sum(e["real"] for e in here), sum(not e["real"] for e in here),
            len(chapters) - len(here), len(filled)), flush=True)

    # Yugioh Top Decks names: some listing rows have no readable name; use the deck page's title
    # ("<name> by <player> | Yugioh Top Decks") or its "Main Archetype" instead.
    named = 0
    for entry in result.values():
        if entry["site"] == "yugiohtopdecks.com" and entry.get("deckType", "").strip() in ("", "Unknown"):
            page = http(entry["source"]) or ""
            title = re.search(r"<title>(.*?) by .*?\|", page)
            lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", page)).splitlines() if l.strip()]
            archetype = lines[lines.index("Main Archetype:") + 1] if "Main Archetype:" in lines else ""
            name = html.unescape(title.group(1)).strip() if title else ""
            entry["deckType"] = name or archetype or "Tournament deck"
            named += 1
    print("named %d Yugioh Top Decks entries from their deck pages" % named)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({"schemaVersion": 3, "revision": REVISION, "keptOriginal": kept_original,
                                    "decks": dict(sorted(result.items()))}, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    real = sum(1 for e in result.values() if e["real"])
    print("wrote %s: %d decks (%d real, %d retro), %d duels keep their original deck" % (
        out_path, len(result), real, len(result) - real, len(kept_original)))


# ---------------------------------------------------------------- apply

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
        line = deck_line(deck)
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
    print("decks: %d bosses, %d normal (%d real, %d retro), %d duels keep their original deck"
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
    if "--cache" in sys.argv:
        CACHE = Path(sys.argv[sys.argv.index("--cache") + 1])
    if mode == "fetch":
        fetch(folder)
    elif mode == "apply":
        apply(folder, "--check" in sys.argv)
    else:
        raise SystemExit(__doc__)
