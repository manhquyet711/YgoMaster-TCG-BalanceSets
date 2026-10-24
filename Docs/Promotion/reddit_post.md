# Reddit post (new thread)

The original v2 thread is archived, so this is a standalone post.

**Where:** r/yugioh, with the flair for fan-made or digital content if there is one. Optionally also r/masterduel; check both subreddits' rules on mods, emulators and self-promotion first, since some don't allow offline mods.
**Before posting:** DM u/Rosehn (the DM in `reddit_reply.md` still works; mention it'll be a new post).
**Attach:** a screenshot of the Solo folders or a duel, or link the gameplay video.

---

## Title (pick one)

1. I made u/Rosehn's 15 balanced old-school character decks playable in Master Duel (free offline mod), then had the AI play 1,050 duels to test the balance
2. Free offline Master Duel mod: pick Yugi, Kaiba, Joey or Pegasus and duel with balanced classic character decks
3. Balanced anime character decks in Master Duel: offline mod plus CPU-vs-CPU win rates for all 15 decks

---

## Body

A few years ago u/Rosehn posted a great set of **balanced old-school character decks**: Yugi, Kaiba, Joey, Mai, Pegasus, Bakura, Jaden, Grandpa's Exodia and more, each true to the anime and built to be roughly even against the others ([2021 post](https://www.reddit.com/r/yugioh/comments/luo915/finally_finished_a_huge_project_a_set_of_balanced/), [2024 finalized lists](https://www.reddit.com/r/yugioh/comments/1epku1s/three_years_ago_i_posted_a_set_of_balanced_old/)).

I wanted to actually play them, so I made a free, **offline** mod for **Master Duel** on Steam:

- **Pick a character, then duel all the others.** Both sides use the exact fixed deck, against the CPU at full strength, 8000 LP each.
- Your collection doesn't matter, and it never connects to Konami's servers.
- All 15 of Rosehn's lists are in card for card. The one exception: **Spellbinding Circle isn't in Master Duel**, so Yugi (Season 1) plays **Shadow Spell** instead.

**How balanced are they?** I had the game's own AI play every matchup against every other: 1,050 duels, half going first each.

| Deck | Win % |
|---|---|
| Rex | 66% |
| Gravekeepers | 63% |
| Joey | 61% |
| Mai | 59% |
| Weevil | 56% |
| Bandit Keith | 55% |
| Bakura, Jaden, Mako | 54% |
| Bonz, Kaiba | 51% |
| Yugi S1 | 47% |
| Yugi S2 | 44% |
| Pegasus | 24% |
| Grandpa | 11% |

**10 of 15 land between 40% and 60%**, which is impressive for decks built around flavour. The caveat is the bottom two. The CPU plays beatdown well, but it can't assemble Exodia or set up Toon World, so Grandpa and Pegasus are much better in human hands than these numbers suggest.

**Also in the mod:**
- **Goat Era Duelists:** 8 more character decks using only Goat-format cards (April 2005).
- **Duel Royale:** Konami's 7 official pre-built decks from the Japanese Duel Royale sets. They tested even more evenly: 6 of 7 between 40% and 60%.
- The **TCG Solo Campaign**, where every chapter uses the real ban list and card pool of its era.

**Links:**
- **Download** (Windows, 253 MB): https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets/releases/latest
  Get the `Balanced-Characters-Master-Duel` zip, not "Source code".
- **Install video** (2 min): https://youtu.be/UNSkqEzeNIc
- **Gameplay demo:** https://youtu.be/utRZhVZrScA
- **Full test results and source:** https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets

It's built on [YgoMaster](https://github.com/pixeltris/YgoMaster) and the [TCG Solo Campaign](https://github.com/vngudu/YgoMaster-TCG) fork. All credit for the character decks goes to u/Rosehn. Fan-made and free, not affiliated with Konami.

Happy to hear which matchups feel off when you play them yourselves. Human results beat CPU results.
