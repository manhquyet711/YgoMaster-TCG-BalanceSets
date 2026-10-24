# Balanced Character Duels

## Current status (0.3.0-prototype, 2026-10-23)

| Area | Status |
|---|---|
| Deck sets | `source-v2` (u/Rosehn 2024, 15 characters, default, played in-game) and `source-v3` (Goat Era Duelists, 8 AI-built Goat-legal decks, packed, not installed yet). `source-v1` retired. |
| Balance testing | CPU vs CPU with the real engine (`npc_balance.py`). v2: 10/15 decks within 40-60%. Tuned v2 test copy: 14/15. v3: round 1 and 2 done, round 3 running. See [Balance/ANALYSIS.md](Balance/ANALYSIS.md). |
| Comparisons | Pegasus B (Relinquished build) and Konami's 7 Duel Royale decks are queued as test-only sets. |
| Solo menu | Grouped into folders, checked in-game: Stories has TCG Campaign and Balanced Characters; Training & Challenges has Format Challenges and Master Duel Basics. Recommended shows the current TCG era and Format Challenge. |
| Launcher / settings | `Start Game.exe` (the redesigned settings editor) is the only launcher: Start Game saves settings, starts the server, then Master Duel. Old `SettingsEditor.exe`, `Start-Balanced.*` and `Open-Balanced-Settings.cmd` removed from the install (backups in `UpgradeBackups\start-game-*`); support files are hidden. Installed. |
| Next | Finish v3 balance, install v3, pick Pegasus version, Duel Royale as its own Solo mode. |

The sections below describe 0.2.2 and are kept as history.

## 0.2.2 status

Development revision: **0.2.2-prototype** (2026-10-22).
Source: F:\ChatGPT\Balanced-Character-Duels.

Fourteen photo-reviewed decks and 182 directed encounters are implemented.
Original Yugi remains blocked by missing Spellbinding Circle; Yugi (Battle City)
is available. No substitute cards or balance edits were added. Kaiba/Joey's
published fingerprints and original battle IDs are unchanged.

The working 0.2.1 client is retained by this upgrade. The user's launcher now
works; installed logs show the 0.2.1 battle click opening the deck/Play panel.
The expanded 0.2.2 maps and actual duels still need gameplay acceptance.

| Phase | Current status | Remaining work |
|---|---|---|
| P0 baseline | Build passes; user confirms launcher works | Ordinary duel/result/restart acceptance |
| P1 deck audit | 15 photos reviewed; 14 decks fully resolved | Original Yugi: Spellbinding Circle absent locally |
| P2/P3 prototype/policy | Implemented, expanded and handler-tested | In-game decks, launch, result and edited-deck attempts |
| P4 roster/presentation | 14 gates, 182 battles, default illustrations | Original Yugi; new portraits/dialogue; each character's in-game smoke test |
| P5 gameplay/balance | Run logger, summary tool, pending manual queue | Actual games/AI capability checks; reviewed adjustments only after evidence |
| P6 optional campaign | Deferred until free-duel acceptance | Design/progression and dialogue |
| P7 release | 0.2.2 upgrade package with backups | Expanded runtime acceptance |

Build: .\Build-Balanced.ps1 -CompilePrototype

Validation: 16 Python tests, 9 compiled deck-policy assertions and real server
handlers exercise every one of the 182 matchups, fixed rules, recipes, names,
free access, all-opponents Goal completion, corrupt content rejection and run
logging. Base campaign remains additive: 954 total chapters, 1203 total duel
settings and 326 packs. See BUILD-0.2.2.log. No automated game simulation ran.

playtest.py creates manual queues and summarizes Data/BalancedCharacters/Logs/
duels.jsonl. Interruptions/incomplete games do not count as losses, test records
are excluded by default, and different content/deck/binary revisions are kept
separate. The first-player field is configured, not automatically observed.
Logs contain no personal player names or account codes.

See RELEASE-0.2.2.md for installation, PHOTO-REVIEW-0.2.2.json for photo evidence,
DECISIONS.md for corrections, and Playtest/QUEUE.csv for the 1,820 pending games.
Earlier BUILD-0.2.0/0.2.1 and native-analysis documents are historical evidence.

Next: install the tested 0.2.2 upgrade with the game closed; open several new
gates, verify deck/Play and complete one duel/result/restart. Then test each
character's Fusion/Ritual/Toon/Gravekeeper/Exodia interactions before screening
balance. Actual AI-vs-AI automation is not established; use the manual queue.
