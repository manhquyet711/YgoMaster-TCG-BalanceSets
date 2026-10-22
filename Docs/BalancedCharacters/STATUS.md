# Balanced Character Duels

Current development revision: **0.2.2-prototype** (2026-10-22).
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
