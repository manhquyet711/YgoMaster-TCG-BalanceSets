# Balanced Characters 0.2.2

Close Master Duel and both settings editors. Extract the ZIP, then double-click
**Install.cmd**. It upgrades the existing G: YgoMaster-BalancedCharacters folder.
After success, run **Start-Balanced.cmd**, open **Stories**, and select a
**Balanced Characters** gate. The gate selects your character; each battle
selects an opponent. All opponent battles are open immediately. The terminal
Goal requires victories over every opponent in that gate.

Included: Yugi (Battle City), Kaiba, Joey, Weevil, Rex, Mako, Mai, Bandit Keith,
Bonz, Pegasus, Marik/Bakura, Gravekeepers, Grandpa and Jaden. This makes 14
characters and 182 directed encounters. Source decks retain their photographed
quantities, including Grandpa's 41 cards and Jaden's 15-card Extra Deck.

Original Yugi remains unavailable: Spellbinding Circle is absent from the
installed card-name tables and passcode map. No substitute was inserted.
Four corrected transcriptions and original-card aliases are documented under
Source/Docs/BalancedCharacters/PHOTO-REVIEW-0.2.2.json and DECISIONS.md.

The update replaces the balanced server, mode content, labels and launcher.
It retains the working 0.2.1 client, settings editor, general/client settings,
ports, collection, personal decks, saves and existing run logs. Mode.enabled
and unknown mode preferences are preserved. The active roster is intentionally
expanded to the 14 verified decks. Replaced files are backed up under
UpgradeBackups/0.2.2-<timestamp>. Installation rolls back if writing fails.

To target another installation:

```powershell
.\Upgrade.ps1 -TargetDirectory 'YOUR BALANCED RUNTIME FOLDER' -DryRun
.\Upgrade.ps1 -TargetDirectory 'YOUR BALANCED RUNTIME FOLDER'
```

Match records are appended to Data/BalancedCharacters/Logs/duels.jsonl.
They contain character/deck identities, version hashes, seeds, configured
starter, rules and client-reported results. They exclude account codes and
personal names. Crashes, timeouts, disconnects and unfinished games do not
count as gameplay losses; surrenders are excluded from win-rate screening.
The engine's actual starter is not observed automatically.

The source snapshot includes playtest.py. With Python 3.9+ installed:

```powershell
python .\Source\Tools\BalancedCharacters\playtest.py summary --runtime 'YOUR BALANCED RUNTIME FOLDER' --output .\PlaytestReport
```

Source/Docs/BalancedCharacters/Playtest/QUEUE.csv contains 1,820 pending
manual games: ten games in each direction for each pair. No games have been
fabricated or automatically simulated. The summary separates different
content, deck and binary versions and excludes development test records.

Build, content, policy, real server-handler tests and installer fixture checks
pass. The expanded in-game maps, all character duels, AI behavior, dialogue,
result/restart flows and balance still require actual gameplay acceptance.
The supplied client continues using the existing card illustrations and
default duel presentation. Custom character portraits/dialogue and an optional
campaign are later milestones, not completed features of this package.

To return to 0.2.1, close the game/editors and run the included Restore.ps1
with the exact backup folder printed by installation. It restores backed-up
files without deleting saves or newly added roster files; restored old mode
content does not select those extra decks.
