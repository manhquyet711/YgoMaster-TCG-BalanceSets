"""NPC-vs-NPC balance runner for a Balanced Characters deck set.

Plays every pair of decks in a revision against each other with the real Master Duel engine
(duel.dll, CPU strength 100 on both sides, 8000 LP, 5-card hands), half the games with each
deck going first, in parallel processes. Results are appended to a log, so a run can be
stopped and continued, and summarised as win rates per deck, going first/second, and per matchup.

Usage:
  python npc_balance.py run --revision source-v3 [--games 20] [--workers 8]
        [--decks-dir <test deck folder>] [--exe <YgoMaster.exe>] [--game-dir <folder next to masterduel_Data>] [--out <folder>]
  python npc_balance.py summary --revision source-v3 [--out <folder>]

--exe defaults to the repository build (YgoMaster/YgoMaster.exe); --game-dir defaults to the
installed balanced runtime (the simulator loads ../masterduel_Data/Plugins/x86_64/duel.dll
relative to it). Output defaults to Docs/BalancedCharacters/Balance/<revision>.

Reading the results: the CPU plays every deck the same way, so a deck far above 50% has more
raw power or plays better for the AI; one far below is weaker or awkward for the AI. Tune the
outliers (in goat_set.py for source-v3), rebuild, and run again.
"""
import argparse
import collections
import concurrent.futures
import itertools
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODE = ROOT / "YgoMaster" / "Data" / "BalancedCharacters"
RESULT = {1: "win", 2: "loss", 3: "draw", 4: "time"}  # DuelResultType, from deck 1's side
DUEL_TIMEOUT_SECONDS = 600


def load_decks(revision, folder=None):
    decks = {}
    file_names = {}
    for path in sorted(Path(folder or MODE / "Decks" / revision).glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        ids = {z: [c["cardId"] for c in d.get(z, []) for _ in range(c["quantity"])] for z in ("main", "extra", "side")}
        decks[d["characterId"]] = ids
        if d.get("displayName"):
            file_names[d["characterId"]] = d["displayName"]
    names = {}
    roster = json.loads((MODE / "Roster.json").read_text(encoding="utf-8-sig"))
    for row in roster:
        names[row["id"]] = row.get("displayName", row["id"])
    names.update(file_names)
    return decks, names


def write_deck_files(decks, folder):
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for cid, ids in decks.items():
        doc = {"name": cid, "m": {"ids": ids["main"], "r": [1] * len(ids["main"])},
               "e": {"ids": ids["extra"], "r": [1] * len(ids["extra"])},
               "s": {"ids": ids["side"], "r": [1] * len(ids["side"])}}
        path = folder / (cid + ".json")
        path.write_text(json.dumps(doc), encoding="utf-8")
        files[cid] = path
    return files


def play(exe, game_dir, deck1, deck2, seed, deck1_first):
    start = time.time()
    try:
        proc = subprocess.run([str(exe), "--cpucontest-sim", str(deck1), str(deck2), str(seed),
                               "true" if deck1_first else "false", "100"],
                              cwd=str(game_dir), capture_output=True, timeout=DUEL_TIMEOUT_SECONDS,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = 4
    return RESULT.get(code, "error:%d" % code), round(time.time() - start, 1)


def run(args):
    decks, names = load_decks(args.revision, args.decks_dir)
    out = Path(args.out)
    files = write_deck_files(decks, out / "decks")
    log = out / "results.jsonl"
    done = collections.Counter()
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if not r["result"].startswith("error"):
                done[(r["a"], r["b"], r["aFirst"])] += 1
    jobs = []
    rng = random.Random(args.seed)
    for a, b in itertools.combinations(sorted(decks), 2):
        if args.only and args.only not in (a, b):
            continue
        for i in range(args.games):
            a_first = i % 2 == 0
            if done[(a, b, a_first)] > 0:
                done[(a, b, a_first)] -= 1
                continue
            jobs.append((a, b, a_first, rng.randrange(1, 2 ** 31)))
    total = len(jobs)
    print("%d decks, %d pairs, %d games per pair: %d duels to play with %d workers" % (
        len(decks), len(set((a, b) for a, b, _, _ in jobs)), args.games, total, args.workers), flush=True)
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool, log.open("a", encoding="utf-8") as fh:
        futures = {pool.submit(play, args.exe, args.game_dir, files[a], files[b], seed, a_first): (a, b, a_first, seed)
                   for a, b, a_first, seed in jobs}
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            a, b, a_first, seed = futures[fut]
            result, secs = fut.result()
            fh.write(json.dumps({"a": a, "b": b, "aFirst": a_first, "seed": seed, "result": result, "seconds": secs}) + "\n")
            fh.flush()
            if n % 10 == 0 or n == total:
                elapsed = time.time() - started
                print("  %d/%d done (%.0f min elapsed, ~%.0f min left)" % (
                    n, total, elapsed / 60, elapsed / n * (total - n) / 60), flush=True)
    summary(args)


def summary(args):
    decks, names = load_decks(args.revision, args.decks_dir)
    out = Path(args.out)
    rows = [json.loads(l) for l in (out / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    stats = collections.defaultdict(lambda: collections.Counter())
    pair = collections.defaultdict(lambda: collections.Counter())
    errors = 0
    for r in rows:
        if r["result"].startswith("error"):
            errors += 1
            continue
        a, b = r["a"], r["b"]
        res = r["result"]
        for me, other, mine, first in ((a, b, res, r["aFirst"]), (b, a, {"win": "loss", "loss": "win"}.get(res, res), not r["aFirst"])):
            stats[me]["games"] += 1
            stats[me][mine] += 1
            stats[me]["first_games" if first else "second_games"] += 1
            if mine == "win":
                stats[me]["first_wins" if first else "second_wins"] += 1
            pair[(me, other)]["games"] += 1
            pair[(me, other)][mine] += 1
    pct = lambda w, g: 100.0 * w / g if g else 0.0
    order = sorted(stats, key=lambda c: -pct(stats[c]["win"], stats[c]["games"]))
    lines = ["# NPC-vs-NPC balance: %s" % args.revision, "",
             "%d duels (%d errors skipped). CPU strength 100 on both sides, 8000 LP, half the games each side first." % (
                 sum(s["games"] for s in stats.values()) // 2, errors), "",
             "| Deck | Games | Win % | Going first | Going second | Draws/timeouts |", "|---|---|---|---|---|---|"]
    for c in order:
        s = stats[c]
        lines.append("| %s | %d | **%.0f%%** | %.0f%% | %.0f%% | %d |" % (
            names.get(c, c), s["games"], pct(s["win"], s["games"]), pct(s["first_wins"], s["first_games"]),
            pct(s["second_wins"], s["second_games"]), s["draw"] + s["time"]))
    lines += ["", "Matchups (row deck's win % against column deck):", "",
              "| | " + " | ".join(names.get(c, c).split()[0] for c in order) + " |",
              "|---|" + "---|" * len(order)]
    for c in order:
        cells = []
        for o in order:
            p = pair.get((c, o))
            cells.append("-" if c == o or not p else "%.0f" % pct(p["win"], p["games"]))
        lines.append("| %s | %s |" % (names.get(c, c), " | ".join(cells)))
    flagged = [c for c in order if abs(pct(stats[c]["win"], stats[c]["games"]) - 50) > 10]
    lines += ["", "Outside 40-60%%: %s" % (", ".join("%s (%.0f%%)" % (names.get(c, c), pct(stats[c]["win"], stats[c]["games"]))
                                                for c in flagged) or "none")]
    text = "\n".join(lines) + "\n"
    (out / "SUMMARY.md").write_text(text, encoding="utf-8")
    print(text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["run", "summary"])
    p.add_argument("--revision", default="source-v3")
    p.add_argument("--games", type=int, default=20, help="games per pair (split between going first and second)")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--seed", type=int, default=20261023)
    p.add_argument("--exe", default=str(ROOT / "YgoMaster" / "YgoMaster.exe"))
    p.add_argument("--game-dir", default=str(ROOT.parents[2] / "YgoMaster-BalancedCharacters"))
    p.add_argument("--out", default=None)
    p.add_argument("--only", default=None, help="play only the pairs that include this deck id (for comparison decks)")
    p.add_argument("--decks-dir", default=None,
                   help="test decks folder instead of Data/BalancedCharacters/Decks/<revision> (e.g. Testing/source-v2-tuned)")
    args = p.parse_args()
    args.out = args.out or str(ROOT / "Docs" / "BalancedCharacters" / "Balance" / args.revision)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    {"run": run, "summary": summary}[args.command](args)


if __name__ == "__main__":
    main()
