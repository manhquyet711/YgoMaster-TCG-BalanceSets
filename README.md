# YgoMaster TCG – Balance Sets

Offline **Yu-Gi-Oh! Master Duel** mod that adds **Balanced Characters**: classic anime characters
duel each other with fixed, photographed old-school decks built to be roughly equal in strength.
It is built on the [TCG Solo Campaign](https://github.com/vngudu/YgoMaster-TCG) and
[YgoMaster](https://github.com/pixeltris/YgoMaster), updated for **Master Duel 2.8.0**.

*Offline only. Progress is not shared with the live game.*

> **Status: 0.3.0 prototype.** Five deck modes in SOLO > Stories, all loaded at once:
> **Balanced Characters** (u/Rosehn's v2 lists), **Goat Era Duelists** (v3, AI-built, Goat-legal),
> **Duel Royale** (Konami's 7 official decks), and **Goat Format Strategies** and **Edison Format Strategies**
> (real tournament decks, tuned). All are tested CPU vs CPU with the real duel engine;
> v3, Duel Royale and the Goat strategies are still being balanced. Results in
> [Docs/BalancedCharacters/Balance/ANALYSIS.md](Docs/BalancedCharacters/Balance/ANALYSIS.md).

## Playing with friends (duel rooms, trading)

`Start Game.exe` has three buttons:

- **Start Game:** play alone (local server, multiplayer off).
- **Host a server:** pick this PC's network address. It turns on multiplayer, opens the server to
  the network (`MultiplayerEnabled`, `BindIP http://*:{BasePort}/`, `SessionServerIP 0.0.0.0`), and
  starts the server and the game. Windows only allows that as administrator, so Start Game restarts
  itself as administrator (confirm the prompt), and Windows Firewall may ask to allow YgoMaster.
- **Join a server:** enter the host's address. It checks the server can be reached, then starts
  only the game, connected to it.

Each player gets their own `MultiplayerToken` automatically. Everyone needs Master Duel 2.8.0 from
Steam and this mod. The easiest way to connect is a private network app all players join
(Tailscale, ZeroTier or Radmin VPN); otherwise forward ports 4989 and 4988 to the host. Progress of
every player is stored on the host. In game: **DUEL > Duel Room (PvP)**. Stories modes stay
player vs CPU. Keep it among friends: Master Duel is Konami's game. Details: [Docs/PvP.md](Docs/PvP.md).

## Videos

- [How to install the Balanced Characters mod (about 2 min)](https://youtu.be/UNSkqEzeNIc)
- [Character balance sets: gameplay demo](https://youtu.be/utRZhVZrScA)
- [Balanced character decks and TCG campaign (Master Duel 2.8.0)](https://youtu.be/rsW_F0inilc)

**Download:** [latest release](https://github.com/manhquyet711/YgoMaster-TCG-BalanceSets/releases/latest). Get
`Balanced-Characters-Master-Duel-<version>.zip` under Assets (the "Source code" downloads won't run).

## Balanced Characters

Open **SOLO > Stories > Balanced Characters** and pick a character gate. The gate chooses the character you play;
each battle node chooses an opponent. All opponents are open from the start, and the gate's Goal
completes after you beat every opponent in it.

**Deck set v2 (default): 15 characters, 210 matchups.** Decks by [u/Rosehn](https://www.reddit.com/user/Rosehn/), from their
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
### Three character modes

Each deck set is its own folder in **SOLO > Stories**, all loaded at the same time (nothing to switch):

| Stories folder | Deck set | Decks |
|---|---|---|
| **Balanced Characters** | `source-v2` | u/Rosehn's updated and finalized 2024 lists, 15 characters (above) |
| **Goat Era Duelists** | `source-v3` | 8 AI-built decks (Yugi, Kaiba, Joey, Mai, Pegasus, Bakura, Marik, Ishizu), every card legal in the April 2005 Goat format. Lists: [Character_Deck_Lists_v3.md](Docs/BalancedCharacters/Character_Deck_Lists_v3.md) |
| **Duel Royale** | `source-v4` | Konami's 7 official Duel Royale decks as printed: Dark Magician, Blue-Eyes, Gearfried, Lava Golem, A Legendary Ocean, Relinquished, Des Gardius. Lists: `Tools/BalancedCharacters/Royale/decklists.json` |
| **Goat Format Strategies** | `source-v5` | 8 top-placing Goat tournament decks (Format Library): Goat Control, Chaos Turbo, Warrior, Chaos Warrior, Chaos Return, Panda Burn, Relinquished, Flip Control. Weak decks got extra tech instead of nerfing the strong ones. Lists and tuning: `Tools/BalancedCharacters/strategy_set.py` |
| **Edison Format Strategies** | `source-v6` | 8 top-placing Edison tournament decks: Blackwing, Gladiator Beast, Lightsworn, Hero Frog, Quickdraw Plant, Machina Gadget, Vayu Turbo, Cat Control. All within 40-60% CPU vs CPU |

Every mode works the same way: the gate picks your deck, each battle node an opponent from the same
mode, 8000 LP, fixed decks, CPU at full strength. Gates are named "Goat Era - …", "Duel Royale - …",
"Goat Format - …" and "Edison Format - …" in those modes. Reference decks in your deck list: "Balanced - …",
"Goat Era - …", "Royale - …", "Goat Format - …", "Edison Format - …".

The original 2021 lists (`source-v1`) are no longer offered; their lists stay in
[Character_Deck_Lists.md](Docs/BalancedCharacters/Character_Deck_Lists.md). v3 is built from
`Tools/BalancedCharacters/goat_set.py` (shared rules: Pot of Greed, Graceful Charity, one MST or
Heavy Storm, at most two premium removal traps, no Goat tournament engines).

How the modes load: each set is a compiled pack in `Data/BalancedCharacters/Revisions/<revision>`,
built by `content.py packs` (part of `Build-Balanced.ps1 -CompilePrototype`). `Mode.json` lists the
loaded sets and their folders (`"sets"`, written by `content.py sets <Data>`); the server loads each pack
on its own, so one bad pack only turns off its own mode. Start Game installs each set's texts
(`ClientData/IDS/IDS_BALANCED_SOURCE_V*.txt`) and gate thumbnails before starting the server.

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
- **Tournament decks in every era:** 435 opponents (351 real decks from the time, 84 retro) across the
  six eras and four challenger gates. Bosses play event winners such as Ng Yu Leung's 2003 World
  Championship deck; normal duels play 2nd-4th place decks from SJCs, YCSs, Nationals and WCQs.
  Each chapter description names the deck, pilot, event, date and placement.
- **Tripled chapter rewards** (600 / 1,200 / 6,000 / 15,000 gems).

## Solo menu

Solo is grouped into mode folders:

- **Stories:** TCG Campaign (DM to VRAINS eras), Balanced Characters, Goat Era Duelists, Duel Royale,
  Goat Format Strategies and Edison Format Strategies.
- **Training & Challenges:** Format Challenges (Goat, Perfect Circle, Edison, HAT, v1.60) and
  Master Duel Basics (the original Tutorial gates).

The two Recommended cards show your current TCG era and Format Challenge. See
[Docs/TCGCampaign/CHANGES.md](Docs/TCGCampaign/CHANGES.md#solo-modes-folders).

## Also included

- **TCG Solo Campaign** from the parent fork: about 300 shop packs with custom art, era progression and dialogue.
  The pack art is compressed per era (995 MB to about 230 MB; see
  [CHANGES.md](Docs/TCGCampaign/CHANGES.md#lighter-pack-art)), so the whole mod is about 285 MB.
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
3. Open `Start Game.exe` (the only file shown in the folder besides `Data`) and press **Start Game**.
   It saves your settings, starts the balanced server on the ports from your settings, then starts Master Duel.
4. In game: **SOLO > Stories > Balanced Characters**.

`Start Game.exe` is also the settings window: a dark window over your game background with a
**Stories Modes** list (pick a mode to see its description and characters; nothing to switch, all five
are always loaded), the on/off switch for the character modes, and settings for
collection, starting gems and campaign rewards. Buttons: **Start Game**, Save, Close. Deck rules above
are fixed by the mode and are not editable. Close the game before saving settings.

The server, client, loader, config files, `Stop-Balanced.ps1` and the log and backup folders are
hidden (Windows hidden attribute) so `Start Game.exe` stands out; `Start Game.exe` re-hides them each
time it opens. Turn on *Show hidden items* in Explorer to see them. Server logs: `LaunchLogs`.
The original YgoMaster `SettingsEditor.exe` and the `Start-Balanced` / `Open-Balanced-Settings`
scripts are no longer shipped (kept for the 0.2.2 upgrade tools in `Tools/BalancedCharacters/Legacy`).

Command line: `--validate` (launch checks only), `--hide`, `--check`, `--self-test <test copy>`,
`--smoke-test`, `--screenshot <png>`, `--deck-set <revision>`.

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
| `Docs/BalancedCharacters/Balance` | CPU-vs-CPU balance results and analysis per deck set |

## Balance testing (CPU vs CPU)

`Tools/BalancedCharacters/npc_balance.py` plays every pair of decks in a set against each other with
Master Duel's own duel engine and AI (strength 100 on both sides, 8000 LP, half the games each side
first), in parallel, and writes win rates, going first/second and a matchup table:

```powershell
python -I Tools\BalancedCharacters\npc_balance.py run --revision source-v3 --games 20 --workers 8
python -I Tools\BalancedCharacters\npc_balance.py summary --revision source-v3
```

It uses `YgoMaster.exe --cpucontest-sim` (run from the installed runtime folder, which has the
game's `duel.dll`). Runs resume from `results.jsonl`. Target: every deck between 40% and 60%.
Options for test-only decks that are not in the game:

| Option / tool | Use |
|---|---|
| `--decks-dir <folder>` | Test a folder of decks instead of the set in `Data` |
| `--only <deck id>` | Play only the pairs with this deck (compare one new deck against a set) |
| `v2_tuning.py build` | Tuned copy of v2 in `Testing/source-v2-tuned` (original v2 unchanged) |
| `goat_set.py compare` | v3 plus comparison decks (`ALT_DECKS`, e.g. Pegasus B) in `Testing/source-v3-compare` |
| `royale_set.py build` | Konami's 7 Duel Royale decks in `Testing/royale` |
| `strategy_set.py build` | Goat and Edison tournament decks in `Testing/strategy-goat` and `Testing/strategy-edison`; `write` makes the game sets (v5, v6) |

Results so far (details and reasons in [ANALYSIS.md](Docs/BalancedCharacters/Balance/ANALYSIS.md)):
v2 has 10 of 15 decks in range (Grandpa 11%, Pegasus 24% lowest; Rex 66% highest); the tuned v2
test copy has 14 of 15. v3 has 6 of 8 after three tuning rounds; Pegasus was then rebuilt around Relinquished (29% to 48%), leaving Marik (64%).

## Manual playtesting

`Docs/BalancedCharacters/Playtest/QUEUE.csv` lists 1,820 manual games (10 per direction for each pair).
After playing, summarise your results with:

```powershell
python .\Tools\BalancedCharacters\playtest.py summary --runtime "<your balanced runtime folder>" --output .\PlaytestReport
```

Crashes, disconnects and unfinished games do not count as losses, and surrenders are left out of win rates.

## Roadmap

- Finish balancing v3 (every deck within 40-60%), then install it and choose Toon Pegasus or Pegasus B
- Ship the tuned v2 as a new deck set if players want it (the original v2 stays)
- Goat Format Strategies: bring Flip Control (29%) into 40-60%
- Play through the playtest queue
- Character portraits and dialogue
- Optional story campaign
- Swap Shadow Spell back to Spellbinding Circle if Master Duel adds it

## Credits

- [pixeltris/YgoMaster](https://github.com/pixeltris/YgoMaster): offline Master Duel server and client
- [vngudu/YgoMaster-TCG](https://github.com/vngudu/YgoMaster-TCG): TCG Solo Campaign
- [Format Library](https://formatlibrary.com) and [Yugioh Top Decks](https://yugiohtopdecks.com):
  historical formats and tournament decklists used for the TCG campaign opponents

### Character decks: u/Rosehn

The v1 and v2 Balanced Characters decks were designed, built and photographed by
**[u/Rosehn](https://www.reddit.com/user/Rosehn/)**. This mod only transcribes their lists into Master Duel.

- Original set (2021, deck revision `source-v1`):
  [Finally finished a huge project: a set of balanced old-school decks](https://www.reddit.com/r/yugioh/comments/luo915/finally_finished_a_huge_project_a_set_of_balanced/)
- Updated and finalized lists (2024, deck revision `source-v2`, the current set):
  [Three years ago I posted a set of balanced old school character decks, today I'm back with my updated and finalized lists!](https://www.reddit.com/r/yugioh/comments/1epku1s/three_years_ago_i_posted_a_set_of_balanced_old/)

The only change made here is Shadow Spell in place of Spellbinding Circle, because that card is not in Master Duel.

### Other deck sets

- **v3 Goat Era Duelists:** designed for this mod (AI-built with Claude), not by u/Rosehn.
- **Duel Royale (test only):** Konami's OCG *Duel Royale Deck Set EX* (2021) and *EX ROUND2* (2022),
  decks built by the University of Yu-Gi-Oh! Tokyo Circle; card lists from
  [Yugipedia](https://yugipedia.com/wiki/Yu-Gi-Oh!_Duel_Royale).

Base mod documentation (settings, PvP, language, Linux, custom content) is in [Docs](Docs).
Licensed under the [MIT License](LICENSE).
