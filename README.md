# YgoMaster TCG – Balance Sets

Offline **Yu-Gi-Oh! Master Duel** mod that adds **Balanced Characters**: classic anime characters
duel each other with fixed, photographed old-school decks built to be roughly equal in strength.
It is built on the [TCG Solo Campaign](https://github.com/vngudu/YgoMaster-TCG) and
[YgoMaster](https://github.com/pixeltris/YgoMaster), updated for **Master Duel 2.8.0**.

*Offline only. Progress is not shared with the live game.*

> **Status: 0.3.0 prototype (character set v2).** The mode builds, installs and has been played in-game
> (map, deck/Play panel and CPU duels work), but balance between all matchups is not tested yet.

## Balanced Characters

Open **SOLO > Stories** and pick a **Balanced Characters** gate. The gate chooses the character you play;
each battle node chooses an opponent. All opponents are open from the start, and the gate's Goal
completes after you beat every opponent in it.

**15 characters, 210 matchups.** Decks by [u/Rosehn](https://www.reddit.com/user/Rosehn/), from their
[updated and finalized 2024 lists](https://www.reddit.com/r/yugioh/comments/1epku1s/three_years_ago_i_posted_a_set_of_balanced_old/) (see [Credits](#credits)):

| | | |
|---|---|---|
| Yugi (Season 1) | Yugi (Season 2) | Kaiba |
| Joey | Weevil | Rex |
| Mako | Mai | Bandit Keith |
| Bonz | Pegasus | Yami Bakura |
| Gravekeepers | Grandpa | Jaden |

**Rules for every balanced duel**

- 8000 LP, 5-card opening hand, shuffled decks, no side decking
- Both players use the exact fixed deck for their character (your collection is not used)
- Same deck for player and CPU, no hidden CPU advantages; the CPU plays at full strength (AI 100)
- Decks keep their photographed card counts, e.g. Jaden's 15-card Extra Deck

**Reference decks:** every player starts with a "Balanced - <character>" copy of all 15 decks in
their deck list, so the recipes can be browsed from day one. No cards are given: the cards you don't
own show as missing, and the deck can't be used in normal duels until you collect them through the
TCG campaign. Each deck is added once; delete one and it stays deleted. When the deck set is updated,
reference decks that are still there get the new cards.

**One substitute:** *Spellbinding Circle* (Yugi, Season 1) does not exist in Master Duel, so it is played
as **Shadow Spell**, the closest old-school card (same lock, plus -700 ATK).

Deck lists: [Character_Deck_Lists_v2.md](Docs/BalancedCharacters/Character_Deck_Lists_v2.md).
The v1 set (14 characters, including Yugi (Battle City) and the Marik/Bakura mix) is kept under
`Decks/source-v1` and can be selected again with `activeDeckRevision` in `Mode.json`.

## TCG campaign: harder and closer to history

The TCG Solo Campaign from the parent fork (450 era duels, 4 challenger gates and a 228-duel post-game)
has been reworked here. Full details: [Docs/TCGCampaign/CHANGES.md](Docs/TCGCampaign/CHANGES.md).

- **Era ban lists, enforced:** every chapter uses the format of its set release (level 01 = LOB 2002
  through level 75 = Eternity Code 2020), including that time's card pool. The server refuses a duel
  when your own deck breaks it.
- **AI strength 100** in every campaign duel.
- **Harder bosses** (the duels that unlock the next pack): CPU at 12,000 LP and always going first;
  the Goat, Perfect Circle, Edison and HAT challenger gates add 16,000 LP and a 6-card hand.
- **Loaner-only era finals:** each era's last boss is played with that era's premade deck.
- **56 premade format decks** in every deck list ("Era 01 Yugi Kaiba Format" … "Era 75 Adamancipator
  Format", plus 5 "Challenger" decks), set to their format, no cards given.
- **Real tournament decks (DM era):** bosses play event winners such as Ng Yu Leung's 2003 World
  Championship deck; normal duels play 2nd-4th place decks from SJCs and Nationals. Each chapter
  description names the deck, pilot, event and placement. Other eras follow.
- **Tripled chapter rewards** (600 / 1,200 / 6,000 / 15,000 gems).

## Also included

- **TCG Solo Campaign** from the parent fork: about 300 shop packs with custom art, era progression and dialogue.
- **Master Duel 2.8.0 update**: hooks, IL2CPP and duel bindings moved to the YgoMaster v1.79 baseline,
  an extended card catalog (13,997 entries) and data fixes. See [UPGRADE-NOTES.md](UPGRADE-NOTES.md).

## Requirements

- Yu-Gi-Oh! Master Duel **2.8.0** from Steam, fully downloaded (finish the in-game tutorial)
- .NET Framework 4.8
- To build: Visual Studio / MSBuild for .NET Framework 4.8, and Python 3.9+ for the content tools

## Install and play

1. Build (below), or use a release package.
2. Put the runtime folder (for example `YgoMaster-BalancedCharacters`) **inside** the game folder,
   next to `masterduel.exe`.
3. Run `Start-Balanced.cmd`. It starts the balanced server and the client on the ports from your settings.
4. In game: **SOLO > Stories > Balanced Characters**.

Settings: `Open-Balanced-Settings.cmd` opens the Balanced Settings Editor (collection, starting gems,
campaign rewards, mode on/off). Deck rules above are fixed by the mode and are not editable.
Close the game before saving settings.

Match results are written to `Data/BalancedCharacters/Logs/duels.jsonl`
(no account codes or names).

## Building from source

```powershell
.\Build-Balanced.ps1 -CompilePrototype   # Balanced Characters build + content, policy and server checks
.\Build-Updated.cmd                      # TCG 2.8.0 build + campaign validation
```

Main locations:

| Path | Contents |
|---|---|
| `YgoMaster/Data/BalancedCharacters` | Roster, source decks, card map, generated chapters |
| `Tools/BalancedCharacters` | Content generator, playtest report tool, validators, settings editor |
| `YgoMaster/Data/TCGCampaign` | Premade era decks and picked tournament decks |
| `Tools/TCGCampaign` | Scripts for era ban lists, AI strength, bosses, era decks and tournament decks |
| `YgoMasterServer`, `YgoMasterClient` | Server and client including the balanced mode hooks |
| `Docs/BalancedCharacters` | Spec, status, decisions, release notes, build logs |

## Playtesting

`Docs/BalancedCharacters/Playtest/QUEUE.csv` lists 1,820 manual games (10 per direction for each pair).
After playing, summarise your results with:

```powershell
python .\Tools\BalancedCharacters\playtest.py summary --runtime "<your balanced runtime folder>" --output .\PlaytestReport
```

Crashes, disconnects and unfinished games do not count as losses, and surrenders are left out of win rates.

## Roadmap

- Play through the playtest queue and tune decks (a separate `balanced-v1` deck revision)
- Character portraits and dialogue
- Optional story campaign
- Swap Shadow Spell back to Spellbinding Circle if Master Duel adds it

## Credits

- [pixeltris/YgoMaster](https://github.com/pixeltris/YgoMaster): offline Master Duel server and client
- [vngudu/YgoMaster-TCG](https://github.com/vngudu/YgoMaster-TCG): TCG Solo Campaign
- [Format Library](https://formatlibrary.com) and [Yugioh Top Decks](https://yugiohtopdecks.com):
  historical formats and tournament decklists used for the TCG campaign opponents

### Character decks: u/Rosehn

Every Balanced Characters deck was designed, built and photographed by
**[u/Rosehn](https://www.reddit.com/user/Rosehn/)**. This mod only transcribes their lists into Master Duel.

- Original set (2021, deck revision `source-v1`):
  [Finally finished a huge project: a set of balanced old-school decks](https://www.reddit.com/r/yugioh/comments/luo915/finally_finished_a_huge_project_a_set_of_balanced/)
- Updated and finalized lists (2024, deck revision `source-v2`, the current set):
  [Three years ago I posted a set of balanced old school character decks, today I'm back with my updated and finalized lists!](https://www.reddit.com/r/yugioh/comments/1epku1s/three_years_ago_i_posted_a_set_of_balanced_old/)
- Rosehn's design philosophy: [swingy, high-variance games with decks that stay true to the anime](https://www.reddit.com/r/yugioh/comments/luo915/comment/gp7oovk/)
- Rosehn is also making [Cardaire](https://store.steampowered.com/app/3124080/Cardaire/), a game inspired by the old-school Yu-Gi-Oh! GBA games.

The only change made here is Shadow Spell in place of Spellbinding Circle, because that card is not in Master Duel.

Base mod documentation (settings, PvP, language, Linux, custom content) is in [Docs](Docs).
Licensed under the [MIT License](LICENSE).
