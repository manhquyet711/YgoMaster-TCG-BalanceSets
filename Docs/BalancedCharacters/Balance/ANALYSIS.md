# Balance analysis (NPC vs NPC)

Measured with `Tools/BalancedCharacters/npc_balance.py`: every pair of decks in a set plays each
other with the real Master Duel engine, CPU strength 100 on both sides, 8000 LP, half the games
with each deck going first. Target: every deck between 40% and 60% overall.

Raw results and full matchup tables:
- v2: [source-v2/SUMMARY.md](source-v2/SUMMARY.md)
- v3 round 1: [source-v3/round1/SUMMARY.md](source-v3/round1/SUMMARY.md)

**Caveat for every result.** The CPU plays every deck the same way: summon, remove, attack.
Combo decks (Exodia, Toons, rituals) score low partly because the AI does not follow their plan.
The numbers measure how well the AI plays a deck, not only the deck's raw power. A low deck may
play better for a human, but the opponents in the game are AI, so these numbers match what a
player faces.

## v2: Original 2021 lists (15 characters), 2026-10-23

1,050 duels (10 per pair), 0 errors. 10 of 15 decks are within 40-60%.

| Deck | Win % | First | Second |
|---|---|---|---|
| Rex | **66%** | 66% | 67% |
| Ishtar (Gravekeepers) | **63%** | 54% | 71% |
| Joey | **61%** | 60% | 61% |
| Mai Valentine | 59% | 57% | 61% |
| Weevil | 56% | 53% | 60% |
| Bandit Keith | 55% | 51% | 59% |
| Yami Bakura | 54% | 54% | 54% |
| Jaden Yuki | 54% | 56% | 51% |
| Mako Tsunami | 54% | 51% | 56% |
| Bonz | 51% | 50% | 53% |
| Kaiba | 51% | 43% | 59% |
| Yugi (Season 1) | 47% | 47% | 47% |
| Yugi (Season 2) | 44% | 44% | 43% |
| Pegasus | **24%** | 31% | 16% |
| Grandpa (Exodia) | **11%** | 9% | 13% |

Why the outliers land where they do:

- **Grandpa (11%):** built to draw all five Exodia pieces, so about half the deck is draw cards
  (Cup of Ace, Jar of Greed, Reckless Greed, Gambler of Legend) with almost no monsters that can
  fight. The AI does not play toward assembling Exodia. It wins 0-20% against almost every deck.
- **Pegasus (24%):** about 15 Toon monsters that need Toon World on the field, plus weak clowns
  and a ritual that rarely comes together. It wins no games against Rex, Gravekeepers, Mai or Mako.
- **Rex (66%):** many solid mid-sized beasts plus strong removal (Dark Hole, Fissure, Mind Control,
  Megamorph, 2 De-Spell). The AI plays this style well. It is the only deck above 60% both first and second.
- **Ishtar (Gravekeepers) (63%):** 3 Necrovalley plus Gravekeeper's Spy and Guard make it hard to
  break through. It is strongest going second (71%).
- **Joey (61%):** steady beatdown with equips and coin-flip cards; only slightly strong.
- **Mai (59%)** is at the edge of the target.

Status: v2 is the original deck lists and is left unchanged. Fixing it would mean a new revision.

## v3: Goat Era Duelists (8 characters, AI-built)

### Round 1, 2026-10-23

560 duels (20 per pair), 0 errors. Deck lists for this round: [source-v3/round1/goat_set.round1.py](source-v3/round1/goat_set.round1.py).

| Deck | Win % | First | Second |
|---|---|---|---|
| Marik Ishtar | **71%** | 64% | 77% |
| Mai Valentine | **61%** | 47% | 74% |
| Ishizu Ishtar | 59% | 53% | 66% |
| Seto Kaiba | 57% | 49% | 66% |
| Joey Wheeler | 56% | 44% | 67% |
| Yami Bakura | 42% | 39% | 46% |
| Yugi Muto | **39%** | 31% | 47% |
| Maximillion Pegasus | **13%** | 9% | 17% |

Most v3 decks win more going second, so the AI may play reactive trap-heavy Goat decks better than it opens.

Changes made for round 2 (in `Tools/BalancedCharacters/goat_set.py`):

| Deck | Problem | Change |
|---|---|---|
| Marik (71%) | Broke the set rule with 3 premium removal traps, plus Snatch Steal | Ring of Destruction to Negate Attack, Snatch Steal to Mind Crush, 1 Mystic Tomato to a 2nd Bowganian |
| Mai (61%) | 3 Elegant Egotist and 2 Phoenix Wing Wind Blast | 2 Egotist, 1 Phoenix Wing; added a 2nd Harpie Lady and Amazoness Fighter |
| Yugi (39%) | Many weak one-offs | 3rd Dark Magician; Celtic Guardian, Book of Secret Arts, Magic Jammer and Draining Shield out; Old Vindictive Magician, Sangan and Torrential Tribute in |
| Pegasus (13%) | Toon cards with only 2 Toon World, weak clowns | 3 Toon World; Ojama Trio, Jigen Bakudan and 3 clowns out; Parrot Dragon, Illusionist Faceless Mage, D.D. Warrior Lady, Sangan, 2nd Manga Ryu-Ran and 2nd Toon Alligator in |

Most later Toon and Harpie support (Toon Gemini Elf, Toon Table of Contents, Cyber Harpie Lady)
is unreleased or forbidden in the Goat list, so Pegasus has few options. He may stay the weakest deck.

### Round 2, 2026-10-23

560 duels, 0 errors. Results: [source-v3/round2/SUMMARY.md](source-v3/round2/SUMMARY.md); deck lists: [source-v3/round2/goat_set.round2.py](source-v3/round2/goat_set.round2.py).

| Deck | Round 1 | Round 2 | First | Second |
|---|---|---|---|---|
| Marik Ishtar | 71% | **64%** | 67% | 60% |
| Seto Kaiba | 57% | **63%** | 60% | 66% |
| Ishizu Ishtar | 59% | 60% | 51% | 69% |
| Joey Wheeler | 56% | 59% | 47% | 70% |
| Mai Valentine | 61% | 55% | 43% | 67% |
| Yami Bakura | 42% | 44% | 41% | 47% |
| Yugi Muto | 39% | **38%** | 39% | 37% |
| Maximillion Pegasus | 13% | **17%** | 14% | 20% |

What it shows:
- **Mai is fixed** (61% to 55%), and Marik came down 7 points but is still above 60%.
- **Kaiba rose** (57% to 63%) without being changed, because the decks around him got weaker. He
  beats Yugi 75% and Pegasus 90%.
- **Yugi did not move.** A 3rd Dark Magician was not enough; the 4 Magnet Warrior cards
  (3 Magnets plus Valkyrion) rarely come together and act as dead draws.
- **Pegasus is still far behind** (17%). Even with 3 Toon World, he wins at most 35% against anyone.

Changes made for round 3:

| Deck | Change |
|---|---|
| Yugi (38%) | Alpha, Beta, Gamma and Valkyrion out; Dark Magician of Chaos, 2 Apprentice Magician and a 2nd Summoned Skull in |
| Kaiba (63%) | 1 Enemy Controller and 1 Lord of D. out; a 2nd Hitotsu-Me Giant and Rude Kaiser in |
| Marik (64%) | 1 Mystic Tomato out; a 2nd Masked Sorcerer in |
| Pegasus (17%) | Parrot Dragon, Illusionist Faceless Mage, Thousand-Eyes Idol and the last Crass Clown out; 2 Mystic Tomato, Magician of Faith and Spirit Reaper in (searchers and defense so he survives until Toon World lands) |

### Round 3

Running; results go to [source-v3/SUMMARY.md](source-v3/SUMMARY.md).

### Pegasus B (comparison deck, test only)

Toon Pegasus stays weak because the CPU plays Toons poorly, so a second Pegasus is tested next to
him: `goat_pegasus_b` in `goat_set.py` (`ALT_DECKS`). Plan: Relinquished / Thousand-Eyes with only
a light Toon touch: 2 Relinquished, 2 Black Illusion Ritual, 2 Sonic Bird, 2 Thousand-Eyes Idol,
Polymerization for Thousand-Eyes Restrict, plus 1 Toon World, Toon Summoned Skull and Toon Alligator,
Mystic Tomato and other support. Same set rules as the other v3 decks.

It plays only against the 8 v3 decks (`npc_balance.py --only goat_pegasus_b`, 20 games each,
including Toon Pegasus head to head), so both Pegasus versions get win rates against the same
opponents. Queued after round 3; results go to `source-v3-compare/SUMMARY.md`.

## Duel Royale (test only, not in the game)

Konami's official pre-built decks for its *Duel Royale* series, made to be played against each other:
*Duel Royale Deck Set EX* (2021) and *EX ROUND2* (2022), built by the University of Yu-Gi-Oh! Tokyo
Circle. Card lists from Yugipedia's set pages, saved in `Tools/BalancedCharacters/Royale/decklists.json`,
built by `royale_set.py build` into `Tools/BalancedCharacters/Testing/royale`. Played as printed
(no ban list), 40 cards each; every card is in Master Duel.

| Deck | Character feel |
|---|---|
| Dark Magician | Yugi |
| Blue-Eyes White Dragon | Kaiba |
| Gearfried the Swordmaster | Joey |
| Lava Golem | Marik |
| A Legendary Ocean | Mako |
| Relinquished (+ Thousand-Eyes Restrict, Sanwitch) | Pegasus |
| Masked Beast Des Gardius | Bakura |

Two test duels finished cleanly. The full test (21 pairs, 20 games each) is queued after Pegasus B;
results go to `royale/SUMMARY.md`. If it tests well it becomes its own Solo mode (folder 2103).
ygo-agent was also checked for these decks: it can play all 155 cards but its trained AI knows only 16 (10%).

## v2 tuned (test only, not in the game)

The original v2 decks stay unchanged in the game, with a copy saved in
[source-v2/original-decks](source-v2/original-decks). The tuned copy is built by
`Tools/BalancedCharacters/v2_tuning.py` into `Tools/BalancedCharacters/Testing/source-v2-tuned`
and tested with `npc_balance.py --decks-dir`. Results go to [source-v2-tuned/SUMMARY.md](source-v2-tuned/SUMMARY.md).

| Deck | Original | Change |
|---|---|---|
| Grandpa | 11% | Keeps Exodia; Emergency Provisions x2, Card Trader, Dark Factory, Backup Soldier, Second Coin Toss and an Ordeal of a Traveler out; Swords of Revealing Light, 2 Big Shield Gardna, Spirit Reaper, Nimble Momonga, Messenger of Peace and Marshmallon in |
| Pegasus | 24% | 2 Dream Clown, 2 Crass Clown, Dark Rabbit, Jigen Bakudan and Toon Defense out; 3 Toon Table of Contents, Mind Control, Magic Cylinder, Toon Kingdom and Shadow Spell in |
| Rex | 66% | Dark Hole, Mind Control and 1 De-Spell out; Little D, Sword Arm of Dragon and Miracle Jurassic Egg in |
| Gravekeepers | 63% | 1 Necrovalley and Dark Hole out; Gravekeeper's Vassal and Gravekeeper's Servant in |
| Joey | 61% | Kunai with Chain out; Little-Winguard in |

### Tuned v2 results, 2026-10-23

1,050 duels (10 per pair), 0 errors. **14 of 15 decks are within 40-60%** (the original had 10 of 15).

| Deck | Original | Tuned |
|---|---|---|
| Joey | 61% | 58% |
| Rex | 66% | 58% |
| Mai Valentine | 59% | 56% |
| Yami Bakura | 54% | 56% |
| Jaden Yuki | 54% | 54% |
| Bandit Keith | 55% | 53% |
| Mako Tsunami | 54% | 53% |
| Weevil | 56% | 51% |
| Ishtar (Gravekeepers) | 63% | 49% |
| Bonz | 51% | 49% |
| Pegasus | 24% | **47%** |
| Kaiba | 51% | 46% |
| Yugi (Season 1) | 47% | 45% |
| Yugi (Season 2) | 44% | 41% |
| Grandpa (Exodia) | 11% | **31%** |

- **Pegasus doubled** (24% to 47%): 3 Toon Table of Contents find Toon World, so his Toons get played.
- **Grandpa nearly tripled** (11% to 31%) but is still the weakest: the stall cards keep him alive, yet the
  CPU still does not dig for Exodia. A next step would be more stall or a few more searchers.
- **Rex and Gravekeepers came down** into range without being weakened too far.
- The spread is now 31-58%, against 11-66% before.

## Other AIs (checked, not used)

YGOPro itself has no AI. **EDOPro's WindBot Ignite** ([ProjectIgnis/windbot](https://github.com/ProjectIgnis/windbot))
is scripted per deck: about 47 built-in decks, almost all modern. Any other deck falls back to
generic play, where most unknown cards are never summoned or activated, so our decks would mostly
measure its gaps. The Master Duel CPU used here knows every card and is the AI players face in the game.

### ygo-agent

[ygo-agent](https://github.com/sbl1996/ygo-agent) is a trained neural-network AI for YGOPro that
can play AI vs AI with custom decks. All 442 v2 cards and 195 v3 cards are playable in its engine,
but its released model was trained on 33 modern decks (863 cards) and knows only 27 of our v2
cards and 12 of our v3 cards (6%). It also needs Linux (WSL2). Not used: its results would mostly
measure the cards it does not know.

## How to rerun

```
python -I Tools/BalancedCharacters/npc_balance.py run --revision source-v3 --games 20 --workers 8
python -I Tools/BalancedCharacters/npc_balance.py summary --revision source-v3
```

Test-only decks (not in the game):

```
python -I Tools/BalancedCharacters/v2_tuning.py build
python -I Tools/BalancedCharacters/npc_balance.py run --revision source-v2-tuned --decks-dir Tools/BalancedCharacters/Testing/source-v2-tuned --games 10
python -I Tools/BalancedCharacters/goat_set.py compare
python -I Tools/BalancedCharacters/npc_balance.py run --revision source-v3-compare --decks-dir Tools/BalancedCharacters/Testing/source-v3-compare --only goat_pegasus_b
python -I Tools/BalancedCharacters/royale_set.py build
python -I Tools/BalancedCharacters/npc_balance.py run --revision royale --decks-dir Tools/BalancedCharacters/Testing/royale
```

A run resumes from `results.jsonl`. Move the old results aside (as in `source-v3/round1`) before
testing changed decks. Compiled decks are immutable once written; for a set that has not shipped,
back up and delete `Data/BalancedCharacters/Decks/<revision>/*.json` before running `content.py resolve`.
