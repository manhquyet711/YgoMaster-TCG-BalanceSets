# TCG campaign changes

Changes made in this fork to the TCG Solo Campaign (gates 2001-2015) to make it harder and closer
to real Yu-Gi-Oh! history. Everything is data plus a few server/client hooks; the scripts in
`Tools/TCGCampaign` re-apply each change and are safe to run more than once.

## Era ban lists per chapter

Every era chapter now uses the format of its own set release. The level comes from the chapter
description ("Progression Level: 07") and maps to the matching regulation in `RegulationInfo.json`
("TCG 07_PGD 2003-08 Yata Format"). Each format has that time's ban list **and** card pool, so cards
released later are forbidden.

| Gate | Levels | Formats |
|---|---|---|
| DM Era (2001) | 01-14 | LOB 2002 (Yugi Kaiba) → FET 2005 (Goat) |
| GX Era (2002) | 15-27 | Reaper 2005 → TeleDAD 2008 |
| 5D Era (2003) | 28-39 | Cat 2009 → Tengu Plant 2011 |
| Zexal Era (2004) | 40-51 | Tengu Plant 2011 → Shaddoll 2014 |
| Arc-V Era (2005) | 52-63 | Burning Abyss 2014 → Draco Zoo 2017 |
| VRAINS Era (2006) | 64-75 | Draco Zoo 2017 → Adamancipator 2020 |

Challenger gates use their named format on the gate: Goat (2012), Perfect Circle (2013),
Edison (2014), HAT (2015); Modern Challenger (2011) uses the current list.

**Enforced by the server.** The game only shows a chapter's ban list, so the server refuses to start
a campaign duel when your own deck breaks it (`INVALID_DECK`). Duel Starter duels, Balanced
Characters, loaner decks and chapters without a ban list are not checked.
Code: `RejectSoloDeckForRegulation` in `YgoMasterServer/Acts/Act_Solo.cs`, called from Solo start
and Duel begin.

Script: `Tools/TCGCampaign/apply_era_rules.py <Data folder>`

## AI strength 100

All 726 TCG campaign duels set `"cpu": 100` (the server default was 97). Balanced Characters duels
also use 100 (`GameServer.BalancedCharacters.cs`, `content.py`, `Mode.json`).

## Harder bosses

The bosses are the duels that unlock the next pack (the 2,000-gem chapters).

| Duels | CPU LP | CPU opening hand | First turn |
|---|---|---|---|
| 75 era bosses (one per level, including each era's final) | 12,000 | 5 | CPU |
| Modern Challenger final duel (20110226) | 12,000 | 5 | CPU |
| Goat, Perfect Circle, Edison, HAT Challenger (48 duels) | 16,000 | 6 | CPU |

Normal duels keep 8,000 LP, 5 cards and a random first player.

The server used to overwrite a duel's first player every time a chapter was opened (random with your
own deck, none after clearing it). Duel files can now set `"firstPlayerLocked": true`; the server then
always uses the file's `FirstPlayer`, also when the client asks for another one
(`SoloLockedFirstPlayer`, `GetSoloDuelSettings` and `Act_DuelBegin` in `YgoMasterServer`).

Script: `Tools/TCGCampaign/apply_boss_rules.py <Data folder>`

## Loaner-only era finals

Each era's last boss must be played with that era's premade deck (see below), not your collection.
The boss reward moves from the own-deck slot (`mydeck_set_id`) to the loaner slot (`set_id`), so it
still pays out and completes the chapter.

| Gate | Final boss | Loaner deck |
|---|---|---|
| DM | 20010082 | Era 12-14 Goat Format |
| GX | 20020076 | Era 27 TeleDAD Format |
| 5D | 20030070 | Era 39-40 Tengu Plant Format |
| Zexal | 20040070 | Era 51 Shaddoll Format |
| Arc-V | 20050070 | Era 63-64 Draco Zoo Format |
| VRAINS | 20060070 | Era 75 Adamancipator Format |

In GX, Zexal and VRAINS the loaner deck is built from that same boss's deck, so those finals are mirror matches.

## Premade era decks

Every player gets 56 decks in their deck list, already set to their format so the deck editor shows
that ban list: 51 era decks named by level and format (e.g. "Era 12-14 Goat Format") and 5
"Challenger …" decks. Each starts from the boss deck of the first level it covers, which is legal for
every level of that format. Like the Balanced reference decks, no cards are given, each deck is added
once, and deleted decks stay deleted (`EraReferenceDecks.json` in the player folder).
With `"DeckListAlphabetical": true` in `Settings.json` the list sorts from Era 01 to Era 75.

Script: `Tools/TCGCampaign/build_era_decks.py <Data folder>` → `Data/TCGCampaign/EraReferenceDecks.json`
Server: `YgoMasterServer/GameServer.EraReferenceDecks.cs`

## Tournament decks (all eras and challenger gates)

Opponents in all six era gates and the Goat, Perfect Circle, Edison and HAT challenger gates play
tournament decks: 435 duels in total, 351 of them real decks from the time and 84 from retro
tournaments. Each chapter description ends with the deck's name, pilot, event, date and placement, e.g.
"Boss deck: Hand Control (Ng Yu Leung, World Championship, August 2003, 1st)" or
"Opponent deck: Earth Beat (Elton Cho, SJC Pomona, April 2005, Top 4)".

| Gate | Real | Retro | Original kept |
|---|---|---|---|
| DM | 27 | 53 | 4 |
| GX | 72 | 2 | 4 |
| 5D's | 44 | 11 | 17 |
| Zexal | 68 | 2 | 2 |
| Arc-V | 51 | 4 | 17 |
| VRAINS | 59 | 3 | 10 |
| Goat Challenger | 12 | 0 | 0 |
| Perfect Circle Challenger | 7 | 5 | 0 |
| Edison Challenger | 0 | 3 | 9 |
| HAT Challenger | 11 | 1 | 0 |

Duels keep their original deck only where no legal tournament deck exists: mostly levels right at a
set release (11, 25, 28-29, 32, 57, 61, 74-75), where nearly every deck of those weeks already uses the
next set's cards. The Modern Challenger post-game (2011) is unchanged. DM formats from 2002 to mid-2003
predate organized play, so DM levels 1-6, 8 and 9 use retro decks.

**DM bosses** were hand-picked (`DM_BOSS_PICKS`); bosses in other eras are picked automatically:
real winners first, then real 2nd/Top 4, then retro winners. The DM bosses:

| Level | Format | Deck | Source |
|---|---|---|---|
| 01 | Yugi-Kaiba | Soul Control | AlephYa2, retro winner |
| 02 | Critter | Muka Muka Turbo | dump truck, retro winner |
| 03 | Treasure | Tomato Control | lollo_8888, retro winner |
| 04 | Imperial | Tomato Control | mihawk, retro winner |
| 05 | Joey-Pegasus | Tomato Control | itsgucci, retro winner |
| 06 | Fiber | Gearfried | Arfio, retro winner |
| 07 | Yata | Hand Control | Ng Yu Leung, World Championship 2003, 1st |
| 08 | Scientist | Scientist Control | WagaMuffin, retro winner |
| 09 | Vampire | Warrior Control | OupsOfCow, retro winner |
| 10 | Chaos | Chaos Control | Theerasak Poonsombat, U.S. Nationals 2004, 1st |
| 11 | Warrior | Earth Beat | Ian Wingrove, SJC Las Vegas 2005, 2nd |
| 12 | Goat | Zombie | Jae Kim, SJC Charlotte 2005, 2nd |
| 13 | Goat | Goat Control | Bryan Coronel, SJC New Jersey 2005, Top 4 |
| 14 | Goat | Goat Control | Max Suffridge, U.S. Nationals 2005, 1st |

**Normal duels** use real decks from the time first (2nd-4th place preferred), then retro decks.
For variety, strategies used least so far in the gate come first, and a level avoids repeating a deck type.

Rules for every pick: legal in the chapter's own format, used only once, every card exists in
Master Duel, and real decks must come from around the level's own period (from the set's release to
a few months after the next one). Archived lists with fewer than 40 main-deck cards are skipped;
old Extra Decks are cut to 15. "Retro" decks come from today's retro-format tournaments (same card
pools, modern players). Names with rare accented letters are simplified for the game font.

Script: `Tools/TCGCampaign/tournament_decks.py fetch <Data folder>` (online, about an hour on a
first run) saves the picks to `Data/TCGCampaign/TournamentDecks.json`, keeping picks already in that
file; every downloaded page is cached in `Tools/TCGCampaign/.cache` (ignored by git), so reruns take
minutes. `tournament_decks.py apply <Data folder>` writes the decks into the duels and chapter texts
without network access.

## Solo modes (folders)

The Solo menu is grouped into mode folders instead of one long list. Master Duel shows a gate's
children inside it (`parent_gate`), and sorts gates by `category` into two sections:
**Stories** (1) and **Training & Challenges** (2).

| Folder gate | Section | Holds |
|---|---|---|
| 2100 TCG Campaign | Stories | Era gates 2001-2006 (DM to VRAINS), unlocking in order as before |
| 2102 Balanced Characters | Stories | Deck set v2's 15 character gates, added by the server at startup |
| 2104 Goat Era Duelists | Stories | Deck set v3's 8 character gates |
| 2103 Duel Royale | Stories | Deck set v4: Konami's 7 Duel Royale decks |
| 2101 Format Challenges | Training & Challenges | Goat, Perfect Circle, Edison, HAT, YgoMaster v1.60 (2011-2015) |
| 2109 Master Duel Basics | Training & Challenges | The original gates: Tutorial (1), 48, and 31 with its gates 22 and 30 |

`Tools/TCGCampaign/solo_modes.py <Data>` adds the folders, their names, descriptions and thumbnails
(`IDS_SOLO.txt`, `SoloGateCards.txt`). Gate IDs do not change, so progress is kept.

Server side:
- **Deck set folders** (`GameServer.BalancedCharacters.cs`, `ApplyBalancedFolder`): the server loads every
  set in `Mode.json` `"sets"` and moves each set's character gates into its folder (2102, 2104, 2103); the
  folder takes the set's first character goal. A folder whose set is not loaded is removed, so no empty
  folder shows.
- **Recommended cards** (`Act_Solo.cs`, `GetRecommendedSoloGates`): each card shows the current gate
  of a mode folder, the first by priority whose goal duel is not cleared and which is visible. Order
  and skipped folders are set in `Settings.json`: `SoloRecommendModes` (default `[2100, 2101, 2102, 2104, 2103]`)
  and `SoloRecommendSkip` (default `[2109]`: the original gates are never recommended).

## Lighter pack art

The campaign's shop art (3 images for each of 326 packs) was about 995 MB of lossless PNG, which
made the mod about 1 GB. `Tools/TCGCampaign/compress_pack_art.py` cut it to about 230 MB, checked in game:

| Images | DM, GX, 5D's (levels 1-39) | Zexal, Arc-V, VRAINS (levels 40-75) |
|---|---|---|
| Shop banners (900x800, no transparency) | JPEG q90 | JPEG q80 at 75% size |
| Pack covers (see-through edges) | PNG re-saved losslessly | 256-colour PNG |

Banners become `.jpg`: the client loads `<name>.jpg` when `<name>.png` is missing.

## Rewards

Chapter clear rewards in `Solo.json` are tripled: 600 / 1,200 / 6,000 / 15,000 gems (reward sets
1 / 4 / 2-3 / 5). Win and loss gems are set per install in `Settings.json` (`DuelRewards`) or with
the Balanced Settings Editor.

## Known issue

Modern Challenger chapter 20110228 ("Card Trader EX") has never been playable: its duel file still
says `"chapter": 600228`, an id from before the campaign's chapters were renumbered.

## Apply order on a fresh copy of the data

```powershell
python Tools\TCGCampaign\apply_era_rules.py   YgoMaster\Data   # ban lists + AI 100
python Tools\TCGCampaign\build_era_decks.py   YgoMaster\Data   # premade era decks
python Tools\TCGCampaign\apply_boss_rules.py  YgoMaster\Data   # boss LP/hand/first turn + loaner finals
python Tools\TCGCampaign\tournament_decks.py apply YgoMaster\Data   # tournament decks + chapter text
python Tools\TCGCampaign\solo_modes.py        YgoMaster\Data   # Solo mode folders
```

`apply_era_rules.py`, `apply_boss_rules.py` and `tournament_decks.py apply` take `--check` to report
what they would change. Build the era decks before applying tournament decks: they are made from
the original boss decks, and rebuilding them afterwards would change their cards (players who already
have them keep their copy unless the file's `revision` changes).

## Sources

- [Format Library](https://formatlibrary.com): format dates, ban lists, historical and retro event top decks
- [Yugioh Top Decks](https://yugiohtopdecks.com): archived decklists from 2004-2005 Shonen Jump Championships, Nationals and Regionals
