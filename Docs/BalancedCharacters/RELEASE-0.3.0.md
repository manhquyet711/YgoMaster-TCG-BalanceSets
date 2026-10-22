# Balanced Characters 0.3.0 - character set v2

Deck revision `source-v2`, from the 15 photos of the "Three years ago I posted a set of balanced
old-school decks" update (local folder `G:\Game\charracter set v2`).

## Roster: 15 characters, 210 encounters

| Character | Change from v1 |
|---|---|
| Yugi (Season 1) | Same list as v1; now playable with Shadow Spell for Spellbinding Circle |
| Yugi (Season 2) | New (replaces Yugi Battle City): +1 Gazelle, Remove Trap, Breaker the Magical Warrior; -Green Phantom King, The Tricky, Mystical Space Typhoon; Extra: Arcana Knight Joker replaces Black Skull Dragon |
| Kaiba | 2 Blackland Fire Dragon, Obelisk the Tormentor replace 2 Blizzard Dragon, Red-Eyes Darkness Metal Dragon |
| Rex | Monster Recovery replaces the second Rush Recklessly |
| Bonz | 2nd De-Spell, Foolish Burial, Mystical Space Typhoon replace Dust Tornado, The Dark Door, Widespread Ruin |
| Yami Bakura | New (replaces Marik/Bakura mix): Beast of Talwar, Michizure replace Lesser Fiend, Exchange |
| Gravekeepers | 3 Gravekeeper's Watcher replace 3 Gravekeeper's Vassal |
| Grandpa | 2 Waboku instead of 3 (40-card deck) |
| Joey, Weevil, Mako, Mai, Bandit Keith, Pegasus, Jaden | Unchanged |

## Decisions

- **Spellbinding Circle -> Shadow Spell (4675)**, requested by the user. Spellbinding Circle is absent
  from the installed card tables. Recorded in `Aliases.json` with `"substitute": true`.
- Duplicate card names resolved to original printings via `YdkIds.txt`: Obelisk the Tormentor
  10000000 -> 4998, Breaker the Magical Warrior 71413901 -> 5655.
- v1 stays immutable under `Decks/source-v1` and `SourceDecks/*.json`; v2 lives in
  `Decks/source-v2` and `SourceDecks/source-v2`. `Mode.json` selects the active revision.

## IDs and saves

- Chapter IDs now use a fixed opponent slot per character (`Ids.json`), so existing battle IDs do not
  move: unchanged pairings (for example Kaiba vs Joey, 20180004) keep their progress.
- New characters: Yugi (Season 2) gate 2031 / NPC 3042 / slot 16; Yami Bakura gate 2032 / NPC 3043 / slot 17.
- Retired gates 2017 (Yugi Battle City) and 2027 (Marik/Bakura) are no longer shown.
- Reference decks: decks given for v1 and still present get the v2 cards in place; deleted ones stay
  deleted; decks the player made with the same name are untouched. `BalancedReferenceDecks.json`
  now records the revision given per character (schema 2; schema 1 files are read as source-v1).
- Duel logs record `deckRevision`.

## Verification

- 17 Python tests, 85 server integration checks and the deck-policy validator pass.
- Dry run of the installed runtime on a copy of the real save: 15 gates / 210 encounters, 15 reference
  decks with correct counts, no cards added to the collection.
- Not yet checked in-game: the new gates and the v2 duels.
