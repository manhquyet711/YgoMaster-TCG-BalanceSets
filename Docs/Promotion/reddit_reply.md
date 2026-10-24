# Reddit reply: u/Rosehn's v2 post

**Where:** a comment on [Three years ago I posted a set of balanced old school character decks, today I'm back with my updated and finalized lists!](https://www.reddit.com/r/yugioh/comments/1epku1s/three_years_ago_i_posted_a_set_of_balanced_old/) (r/yugioh).

**Before posting:**
- Send u/Rosehn a short DM first (template at the bottom). It's their decks, and a heads-up is good manners.
- Check r/yugioh's rules on self-promotion and mods/emulators. If the post isn't allowed as a comment, ask Rosehn whether they'd rather share it themselves.
- Make the GitHub release (zip download) first. The links below assume it exists.

---

## Comment

**I turned your 15 finalized lists into a playable offline mode for Master Duel, and ran every matchup CPU vs CPU to see how balanced they are**

Hi u/Rosehn, these lists are great, so I built a free offline mod around them: **Balanced Characters for Master Duel**. You pick a character, then duel every other character, each side using its exact fixed deck, against the CPU at full strength.

**What it is**
- An offline mod for the Steam version of Master Duel (2.8.0), built on [YgoMaster](https://github.com/pixeltris/YgoMaster) and the TCG Solo Campaign fork. It never connects to Konami's servers, and your real account isn't touched.
- All 15 of your v2 decks, card for card: 210 matchups, 8000 LP, no side decking, and your collection isn't used. The only change: **Spellbinding Circle isn't in Master Duel**, so Yugi (Season 1) plays **Shadow Spell** instead.
- Each deck also appears in your deck list as "Balanced - <name>", so people can browse the recipes.

**The balance test**
I had the game's own duel engine and AI play every pair of your decks against each other (1,050 duels, half going first each). 10 of the 15 decks landed between 40% and 60%:

| Deck | Win % |
|---|---|
| Rex | 66% |
| Ishtar (Gravekeepers) | 63% |
| Joey | 61% |
| Mai | 59% |
| Weevil | 56% |
| Bandit Keith | 55% |
| Bakura / Jaden / Mako | 54% |
| Bonz / Kaiba | 51% |
| Yugi (Season 1) | 47% |
| Yugi (Season 2) | 44% |
| Pegasus | 24% |
| Grandpa (Exodia) | 11% |

Big caveat: the AI plays straightforward beatdown well, but it doesn't pilot combo plans like Exodia or Toon World. So Grandpa and Pegasus are probably much better in human hands than these numbers suggest. The original lists are what's in the mod; I didn't change them. A tuned copy (more stall for Grandpa, Toon Table of Contents for Pegasus) tested at 14 of 15 in range, but it's kept separate, as a test.

**Also in the mod**
- **Goat Era Duelists:** 8 extra character decks I built from Goat-format-legal cards (April 2005).
- **Duel Royale:** Konami's 7 official pre-built decks from the Japanese Duel Royale sets.
- Each set is its own folder in Solo, next to the TCG Solo Campaign.

**Download:** [GitHub release](https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets/releases) · [Source and full results](https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets) · [Setup video](https://youtu.be/UNSkqEzeNIc) · [Gameplay demo](https://youtu.be/utRZhVZrScA)

Full credit for the decks goes to you. The mod's README links back to both of your posts. Thanks for putting these together!

---

## DM to u/Rosehn (send first)

> Hi! I loved your balanced old-school character decks, and I made a free offline Master Duel mod where you can play all 15 v2 lists against each other (fixed decks, vs the CPU). I credited you and linked both of your posts. I also ran every matchup CPU vs CPU and got some win-rate numbers you might find interesting. Would you be OK with me sharing it as a comment on your v2 post? Happy to change anything you'd like first. Repo: https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets
