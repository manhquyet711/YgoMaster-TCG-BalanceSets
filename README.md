# YgoMaster TCG – Balance Sets

Offline **Yu-Gi-Oh! Master Duel** mod that adds **Balanced Characters**: classic anime characters
duel each other with fixed, photographed old-school decks built to be roughly equal in strength.
It is built on the [TCG Solo Campaign](https://github.com/vngudu/YgoMaster-TCG) and
[YgoMaster](https://github.com/pixeltris/YgoMaster), updated for **Master Duel 2.8.0**.

*Offline only. Progress is not shared with the live game.*

> **Status: 0.2.2 prototype.** The mode builds, installs and has been played in-game
> (map, deck/Play panel and CPU duels work), but balance between all matchups is not tested yet.

## Balanced Characters

Open **SOLO > Stories** and pick a **Balanced Characters** gate. The gate chooses the character you play;
each battle node chooses an opponent. All opponents are open from the start, and the gate's Goal
completes after you beat every opponent in it.

**14 characters, 182 matchups:**

| | | |
|---|---|---|
| Yugi (Battle City) | Kaiba | Joey |
| Weevil | Rex | Mako |
| Mai | Bandit Keith | Bonz |
| Pegasus | Marik / Bakura | Gravekeepers |
| Grandpa | Jaden | |

**Rules for every balanced duel**

- 8000 LP, 5-card opening hand, shuffled decks, no side decking
- Both players use the exact fixed deck for their character (your collection is not used)
- Same deck for player and CPU, no hidden CPU advantages
- Decks keep their photographed card counts, e.g. Grandpa's 41-card deck and Jaden's 15-card Extra Deck

**Reference decks:** every player starts with a "Balanced - <character>" copy of all 14 decks in
their deck list, so the recipes can be browsed from day one. No cards are given: the cards you don't
own show as missing, and the deck can't be used in normal duels until you collect them through the
TCG campaign. Each deck is added once; delete one and it stays deleted.

Original Yugi is not included yet: *Spellbinding Circle* is missing from the game's card data,
and no substitute card was inserted. Card transcriptions and decisions are documented in
[Docs/BalancedCharacters](Docs/BalancedCharacters) (`DECISIONS.md`, `PHOTO-REVIEW-0.2.2.json`,
`Character_Deck_Lists.md`).

## Also included

- **TCG Solo Campaign** from the parent fork: 450 duels across the DM, GX, 5D's, Zexal, Arc-V and VRAINS eras,
  era-accurate ban lists, about 300 shop packs with custom art, and a post-game with 228 decks.
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
- Original Yugi once Spellbinding Circle is available

## Credits

- [pixeltris/YgoMaster](https://github.com/pixeltris/YgoMaster): offline Master Duel server and client
- [vngudu/YgoMaster-TCG](https://github.com/vngudu/YgoMaster-TCG): TCG Solo Campaign
- Balance deck set: community photo project of balanced old-school character decks

Base mod documentation (settings, PvP, language, Linux, custom content) is in [Docs](Docs).
Licensed under the [MIT License](LICENSE).
