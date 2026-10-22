# Manual gameplay acceptance and balance screening

No real games have been entered into this queue. Automated server-handler
tests are separate evidence and do not count as gameplay or AI results.

First run a smoke pass with each of the 14 characters as player and CPU.
Verify gate illustration/name, every opponent's deck preview, Play, a complete
duel, result and restart. All opponent battles should be selectable without
winning earlier map nodes. Goal should remain locked until all opponents in
that gate have been beaten. Confirm that normal Stories campaigns still work.

Before screening win rates, record actual CPU behavior for these decks/cards:

| Deck | Relevant photographed cards | Required observation |
|---|---|---|
| Yugi (Battle City) | Polymerization, Dark Paladin, Chimera, Gaia the Dragon Champion | Fusion use, materials and target choice |
| Kaiba | Polymerization, Blue-Eyes Ultimate Dragon, Lord of D., The Flute of Summoning Dragon | Fusion/summoning sequences and tribute choices |
| Joey | Polymerization, Thousand Dragon, Time Wizard | Fusion and situational effect decisions |
| Weevil | Petit Moth, Cocoon of Evolution, Great Moth, DNA Surgery, Insect Barrier | Evolution setup, stall timing and type interaction |
| Rex | Jurassic World, Dark Driceratops, Black Tyranno | Tribute choices and battle decisions |
| Mako | A Legendary Ocean, The Legendary Fisherman, Fortress Whale, Fortress Whale's Oath | Field-dependent choices and Ritual setup |
| Mai | Elegant Egotist, Harpie Lady Sisters, Hysteric Party | Summoning and revival timing |
| Bandit Keith | 7, 7 Completed, Limiter Removal, Barrel Dragon | Equips, effect timing and removal decisions |
| Bonz | Book of Life, Call of the Mummy, Vampire Lord | Revival and tribute sequences |
| Pegasus | Toon World, Toon monsters, Relinquished, Black Illusion Ritual | Toon restrictions and Ritual setup |
| Marik/Bakura | Destiny Board, Spirit Messages, Dark Sanctuary, Dark Necrofear | Alternate-win setup and summoning choices |
| Gravekeepers | Necrovalley, Royal Tribute, Gravekeeper's Chief | Field/graveyard interaction decisions |
| Grandpa | Exodia pieces, Card Trader, Wandering Mummy | Draw/search decisions, stalling and alternate win |
| Jaden | Polymerization, Miracle Fusion, Fusion Gate, all 15 Extra Deck cards | Fusion material selection and situational Fusion choices |

For a failure, record runId, character direction, visible starter, seed from
the matching start log, turn, replay path and a precise observation. Do not
change source-v1 to make the AI pass. Reproduce the failure and distinguish
engine effects, UI problems, CPU decisions and the deck's own limitations.
Configured CPU 97 is retained; it is not a verified difficulty scale.

QUEUE.csv contains ten trials for each directed matchup: 91 pairs x 20 games
= 1,820 pending games. It does not force seeds/starters or drive the game.
Use the logged actual configuration and record who visibly started. Do not
infer the observed starter from the configured field alone.

Run playtest.py summary against the installed runtime to summarize recorded
human-vs-CPU results. Normal completed wins/losses are eligible; surrenders,
draws, failures, timeouts and disconnects are shown separately or excluded.
Unfinished starts remain incomplete. Development test records are excluded by
default. Logs with different versions/fingerprints are not pooled together.

No universal 50% per-pair target is imposed. Review outliers with human play
before proposing balanced-v1 changes. Future changes need an explicit reason,
affected matchup evidence, a separate deck revision and a regression pass.
