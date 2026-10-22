# Balanced Character Duels — AI implementation specification

Version: 1.0 | Prepared: 2026-10-21 | Status: SPECIFICATION ONLY

Implementation update 2026-10-22: this original specification is retained as
the target contract. Current source S is F:\ChatGPT\Balanced-Character-Duels;
STATUS.md and RELEASE-0.2.2.md describe actual completion. Fourteen verified
characters/182 encounters are implemented. Original Yugi is blocked by missing
Spellbinding Circle. Connected opponent chains plus terminal Goals supersede
the early root-only map proposal. Kaiba's reviewed Main count is 40. No gameplay
balance, custom dialogue or optional campaign completion is implied.

## 1. Mission and completion contract

Implement an offline Master Duel mode containing the user's 15 balanced old-school character decks. Preserve character identity, weaker situational cards, and slower dramatic games. Use the existing Master Duel engine and updated TCG fork. Offline CPU play comes first. Multiplayer, historical rules, native AI replacement, anime effects, and a new rendering engine are outside this release.

This file authorizes a future implementation agent to implement the selected phase when the user requests it. It does not claim any proposed file or feature already exists. Existing paths and method names below were inspected; proposed names are explicitly marked NEW. Re-read the actual source before editing because it can change after this specification.

Complete phases in order. A phase with a failed dependency is BLOCKED, not complete. Report completed code/data work separately from unperformed in-game checks. Never claim compatibility, AI competence, historical accuracy, or deck balance from compilation alone.

## 2. Paths and baseline

Known working source root S:
`F:\ChatGPT\YgoMaster-TCG-update\upstream`

Original user project O:
`G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-TCG-release20250630`

Game root G:
`G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel`

Installed updated mod R:
`G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-TCG-Updated-2.8.0`

Deck-photo source P:
`G:\Game\Joey\Desk list`

All relative paths below are relative to S unless stated otherwise. Runtime data root is `YgoMaster/Data`. Confirm local permissions before installation; prepare a package in a writable location if G is read-only. Do not silently use a different mod installation. Preserve original campaign data and player saves. Develop a separate runtime profile/directory for this mode; do not change the user's normal TCG progress.

Inspected baseline: .NET Framework 4.8 client; explicit Compile Include project entries; `Build-Updated.ps1 -Validate` builds Release/x64 and invokes `Tools/ValidateCampaign.cs`. Native loader is supplied separately and should remain unchanged. Server project is `YgoMasterServer/YgoMaster.csproj`, NOT `YgoMasterServer/YgoMasterServer.csproj`.

At inspection, G had `LocalSave` but no `LocalData`. Re-check before concluding content is still missing. Obtain game content through the user's official installation; do not invent replacement assets or create empty folders and call the issue fixed.

## 3. Decisions and defaults

Confirmed intent: 15 pictured decks, character identity, comparable strength, mostly pre-2007 cards, offline AI first. Preserve the source lists, including Jaden and any later cards actually pictured. Do not impose a strict date cutoff that deletes cards from those lists.

Implementation defaults, revisable by the user: 8000 LP, five opening cards, shuffle enabled, normal duel type, no side decking, all supplied characters accessible in free duel, modern game engine effects/rules. No reward or crafting prerequisite for a supplied fixed deck. CPU setting begins with the existing default 97 and no special cpuflag; this is a baseline configuration, not a documented difficulty scale.

Fixed-deck mode uses exact per-zone card multisets; order and cosmetic finish do not affect identity. A whitelist alone is insufficient. Source deck version `source-v1` is immutable after transcription verification; balancing creates a separate `balanced-v1` revision with a change log. Initial player and CPU copies use identical lists. No hidden CPU-only advantages.

## 4. Roster and stable identifiers

Use these string IDs across source data, logs, and assets. Integer game IDs are allocated separately after collision checking.

| ID | Display name | Main | Extra |
|---|---|---:|---:|
| yugi | Yugi | 40 | 0 |
| yugi_battle_city | Yugi — Battle City | 40 | 4 |
| kaiba | Kaiba | 41 | 3 |
| joey | Joey | 40 | 3 |
| weevil | Weevil | 40 | 0 |
| rex | Rex | 40 | 0 |
| mako | Mako Tsunami | 40 | 0 |
| mai | Mai Valentine | 40 | 0 |
| bandit_keith | Bandit Keith | 40 | 0 |
| bonz | Bonz | 40 | 0 |
| pegasus | Pegasus | 40 | 2 |
| marik_bakura | Marik/Bakura | 40 | 0 |
| gravekeepers | Ishtar — Gravekeepers | 40 | 0 |
| grandpa | Grandpa — Exodia | 41 | 0 |
| jaden | Jaden Yuki | 40 | 15 |

These are previous transcription totals, not newly verified card lists. Resolve `Character_Deck_Lists.md` from the user's saved files, read its current contents, and compare uncertain entries against P. Do not regenerate card names from memory. Ritual monsters stay in Main; pictured Fusion cards go in Extra.

## 5. Exact file inventory

### Existing files: intended touch points

| File | Required scope |
|---|---|
| `YgoMasterServer/GameServer.State.cs` | Load validated balanced-mode configuration/catalog after ordinary data load; invoke generated Solo overlay after LoadSolo/LoadSoloDuels; mode-disabled path must preserve existing behavior. |
| `YgoMasterServer/Acts/Act_Duel.cs` | GetSoloDuelSettings, CreateSoloDuelSettingsInstance, Act_DuelBegin, Act_DuelEnd are the launch/result integration points. Enforce fixed settings after ordinary deck/name overrides and before ActiveDuelSettings/response assignment. |
| `YgoMasterServer/Acts/Act_Solo.cs` | Read generated gate/chapter metadata; prevent normal progression locks from hiding free-duel chapters; keep normal campaign behavior for other IDs. |
| `YgoMasterServer/GameServer.Writers.cs` | Only if deck UI needs balanced-mode validity labels; UI validity is supplementary, not enforcement. |
| `YgoMasterServer/Infos/DeckInfo.cs` | Reuse parsing, CopyFrom, MainDeckCards/ExtraDeckCards/SideDeckCards. Do not globally replace IsValid or globally waive ownership checks. |
| `YgoMasterServer/DuelSettings.cs` | Reuse Deck, life, hnum, names, cpu, cpuflag, bgms, dialog_intro/outro, PreserveP1 fields. Add fields only if required and ensure wire serialization remains compatible. |
| `YgoMasterServer/YgoMaster.csproj` | Add NEW server Compile Include entries; avoid unintended client compilation. |
| `YgoMasterClient/DuelStarter.cs` | Optional later character selector; initial version uses Solo gate selection. Raw duelStarterData must not override fixed balanced chapters. |
| `YgoMasterClient/AssetHelper.Solo.cs` | Reuse gate art/background loader; extend only if existing paths cannot represent assets. |
| `YgoMasterClient/SoloVisualNovel.cs` and `SoloVisualNovelChapterView.cs` | Reuse existing dialogue format and loader. Inspect actual baseDir and a working sample before creating dialogue files. |
| `YgoMasterClient/ClientSettings.Text.cs` | Only if additional interface labels cannot use existing IDS/text assets. |
| `YgoMasterClient.csproj` | Add new client files only when needed; it uses explicit Compile Include. |
| `Build-Updated.ps1` | Add optional balanced validation/package checks after current checks, not instead of them. |

`YgoMasterServer/Infos/SoloInfo.cs` is commented-out/unused. DO NOT implement the feature there. Active Solo logic is in Act_Solo.cs and GameServer.State.cs.

### NEW authored data (canonical inputs; never generated in place)

Place under `YgoMaster/Data/BalancedCharacters/`:

| Path | Contents |
|---|---|
| `Mode.json` | schemaVersion, enabled, contentVersion, rosterVersion, defaults, freeDuel gate mode, active deck revision. |
| `Roster.json` | Array of 15 character records: id, displayName, deckRevision, deckFile, presentationId. |
| `SourceDecks/<id>.json` | Verified card names/quantities, zone, source image filename, uncertainty status. |
| `Decks/source-v1/<id>.json` | Resolved canonical card IDs/quantities per zone. |
| `Decks/balanced-v1/<id>.json` | Created only when justified adjustments exist; no silent fallback to a different revision. |
| `CardMap.csv` | sourceName, normalizedName, masterDuelId, passcodeIfKnown, resolutionStatus, evidence, effectNote. |
| `Presentation.json` | Character names and validated existing portrait/field/sleeve/music references; optional dialogue references. |
| `Ids.json` | Allocated gate/chapter/NPC IDs and ordered player/opponent mappings. |
| `BalanceChanges.csv` | revision, characterId, cardId, oldQuantity, newQuantity, reason, evidenceRunId. |

NEW generated outputs go under `Tools/BalancedCharacters/Generated/`, never into canonical inputs. Generated Solo overlays remain separate from the original Solo.json.

NEW implementation files:
- `YgoMasterServer/GameServer.BalancedCharacters.cs`: partial GameServer integration, load state, overlay merge, chapter lookup.
- `YgoMasterServer/BalancedCharacters/CharacterCatalog.cs`: parse/validate immutable canonical data.
- `YgoMasterServer/BalancedCharacters/FixedDeckPolicy.cs`: construct trusted settings and verify exact multisets.
- `YgoMasterServer/BalancedCharacters/DuelRunLogger.cs`: append run/result records scoped to balanced chapters.
- `Tools/BalancedCharacters/Resolve-CardMap.ps1`: resolve names/IDs, emit unresolved report; no guessed IDs.
- `Tools/BalancedCharacters/Build-Content.ps1`: validate inputs and generate overlay/duel files deterministically.
- `Tools/BalancedCharacters/ValidateBalancedCharacters.cs`: meaningful schema, content, integration-policy tests.
- `Tools/BalancedCharacters/Package-Mode.ps1`: create isolated distributable plus manifest.
- `Docs/BalancedCharacters/STATUS.md`: phase checklist, evidence, blockers, next action.
- `Docs/BalancedCharacters/DECISIONS.md`: user decisions, implementation defaults, unresolved matters.
- `Docs/BalancedCharacters/CARD-AUDIT.csv`: per-card availability, uncertain names, observed errata/combo issues.
- `Docs/BalancedCharacters/PLAYTEST.csv`: in-game test evidence.
- `Docs/BalancedCharacters/INSTALL.md`: installation, launch, rollback, saved-profile location.

## 6. Canonical data contract

These are NEW schemas, not existing YgoMaster wire formats. Tools convert them to the game's inspected structures.

Example resolved deck (illustrative IDs are deliberately omitted):
```json
{
  "schemaVersion": 1,
  "characterId": "kaiba",
  "revision": "source-v1",
  "main": [{"cardId": 0, "quantity": 1}],
  "extra": [],
  "side": [],
  "expectedMainCount": 41,
  "expectedExtraCount": 3
}
```
The sample above is NOT playable: cardId 0 must fail validation. Populate real IDs and full quantities from verified lists. Expand quantities into repeated IDs for `Main.CardIds` and `Extra.CardIds`; emit equally sized `Rare` arrays using valid cosmetic styles. Existing Solo duel files use that long-key deck format. Do not confuse cosmetic style with N/R/SR/UR catalog rarity.

Mode defaults: life [8000,8000], hnum [5,5], noshuffle false, Type 0, MyType 0, cpu 97, cpuflag null. Choose FirstPlayer once at duel creation, not on each settings lookup. Preserve the selected value in the active duel and logs. Generate fresh random seeds in normal play; permit explicit seeds only through the developer test path. Do not inherit tutorial fields from 10001.json: that sample contains fixed seed, AttackOnly, 2000 LP, no shuffle, and abnormal hands.

ID allocation: scan existing gates, chapters, NPC records, and custom targetChapterId before allocating. Persist the allocation in Ids.json; reject collisions rather than overwrite. Required invariant from GetChapterGateId: chapterId / 10000 == gateId (integer division). Do not hardcode an unverified numeric range. String character IDs remain stable if integer IDs need migration.

## 7. Phase P0 — baseline and reproducibility

Inputs: S, O, G, R. Do not modify game data in this phase.

Tasks:
1. Read applicable AGENTS.md; inventory exact source/runtime versions and build tools. Hash masterduel.exe, GameAssembly.dll if present, duel engine binary if present, and the three mod binaries. Record actual discovered names, sizes, hashes, timestamps in NEW `Docs/BalancedCharacters/BASELINE.json`.
2. Run `powershell -NoProfile -File .\Build-Updated.ps1 -Validate` from S. Save exit codes and concise output in STATUS.md. If blocked, record the actual error and missing dependency.
3. Re-check downloaded content path used by the launcher. Inspect crash logs if startup fails. A successful file-presence check is not a successful boot.
4. On a usable Windows game session, run home -> deck editor -> ordinary CPU duel -> result -> restart.
5. Establish an isolated runtime directory/profile for testing and document how its player saves differ from normal TCG saves. Verify the actual player-data path resolution before copying anything.

Done: build/data checks pass, runtime baseline demonstrated, or exact runtime blocker recorded. Data preparation P1 may proceed while runtime is blocked; game-dependent acceptance cannot pass.

## 8. Phase P1 — exact deck transcription and ID audit

Files: SourceDecks/*.json, CardMap.csv, CARD-AUDIT.csv, Resolve-CardMap.ps1, Decks/source-v1/*.json.

Tasks:
1. Resolve/read Character_Deck_Lists.md from saved files; associate each deck with its source photo in P. Verify uncertain entries visually. Preserve provenance and totals.
2. Inspect `YgoMaster/Data/CardList.json`, `CardData`, `CardFiles`, `YdkIds.txt` to determine which contain IDs, names, and mappings in this installation. Do not assume CardList.json is an English name database. Use available decoded game names or verified mapping exports where needed.
3. Normalize punctuation/case for suggestions only. Distinct card versions must not be auto-merged. Require an exact verified mapping for every entry.
4. Emit a report for missing/ambiguous cards and changed effects. Do not substitute another card to make validation green.
5. Generate immutable source-v1 decks. Check quantities, IDs, zones, counts, duplicate entries, side count zero, maximum legal copies under the intended custom rules. An apparent source anomaly must be flagged rather than silently repaired.

Done: 15 source decks accounted for; each playable deck has zero unresolved IDs; totals match verified photos. A blocked character remains explicitly unavailable, not partially imported. Prototype can proceed if yugi/kaiba/joey are complete.

## 9. Phase P2 — content compiler and three-character prototype

Files: Mode.json, Roster.json, Presentation.json, Ids.json, Build-Content.ps1, CharacterCatalog.cs, GameServer.BalancedCharacters.cs, GameServer.State.cs, server csproj.

Implementation:
1. Load Mode.json only if present. enabled=false must preserve ordinary runtime behavior. Invalid enabled content disables balanced launches with a clear error; never launch an empty/default deck.
2. Implement catalog validation and immutable trusted deck templates. Copy templates per duel; do not mutate SoloDuels shared instances or catalog objects.
3. Generate three player-character gates (Yugi, Kaiba, Joey), each with one opponent chapter per other prototype character: six directed encounters. Initial version excludes self-matchups. Selecting a gate chooses the player's character; selecting a chapter chooses the opponent. This avoids requiring a new client screen.
4. Base generated gate/chapter wire dictionaries on a working normal duel gate, not on unused SoloInfo.cs or a tutorial. Include category; map NPC metadata and story deck IDs consistently with LoadSoloDuels.
5. Runtime overlay: merge generated gates/chapters into in-memory SoloData and generated trusted duel templates into SoloDuels AFTER original loading. Reject collisions. Do not overwrite Solo.json or globally modify chapter completion state.
6. Free-duel chapters must be visible and selectable without modifying unrelated campaign locks. Use rental/loaner-only entry where possible; policy in P3 still enforces both routes.
7. Inspect how Solo.detail constructs deck previews and story_deck_id. Ensure preview, recipe and actual launched decks all match; generated overlays must perform the same required registration as ordinary loaded duels.

Done: three gates/six encounters appear; each shows and launches intended player/opponent decks; result/restart works. Runtime completion waits for P3 enforcement.

## 10. Phase P3 — fixed-deck enforcement and bypass prevention

Files: FixedDeckPolicy.cs, GameServer.BalancedCharacters.cs, Act_Duel.cs, optional scoped changes to Act_Solo.cs, ValidateBalancedCharacters.cs.

Proposed API responsibilities (NEW, adapt signatures to actual accessible types):
- `TryGetEncounter(chapterId, out encounter)` resolves only registered balanced chapters.
- `BuildTrustedSettings(encounter, catalog)` creates fresh settings and exact decks from server data.
- `ApplyBalancedPolicy(player, encounter, settings)` applies trusted decks/rules/presentation after ordinary customization.
- `ValidateFixedDeck(actual, expected)` compares dictionaries cardId->quantity separately for Main/Extra/Side; ignores order and cosmetic style.

Launch ordering in Act_DuelBegin:
1. Parse mode and chapter; resolve membership using server encounter registry.
2. For a registered balanced Solo chapter, build trusted settings regardless of client duelStarterData. Reject contradictory mode/chapter requests with an existing client-compatible error pattern. Inspect neighboring handlers to choose the actual response/error code; do not invent a wire error code.
3. Normal code may apply player deck/name/FirstPlayer overrides. Before assigning ActiveDuelSettings and emitting Duel, reapply balanced trusted decks/rules and validate. Never trust client deck IDs, LP, hand sizes, cpu/cpuflag, Type, no-shuffle or claimed roster revision.
4. Ensure global CustomDuel.json targetChapterId cannot replace a balanced encounter on completion/replay. Bypass that override for registered balanced chapters in GetSoloDuelSettings.
5. Ensure IsMyDeck paths in CreateSoloDuelSettingsInstance cannot substitute an edited personal deck. Loaner use must not require owning the supplied cards. Use scoped trusted rental decks; do not set DisableDeckValidation globally.
6. Maintain character display name against Act_DuelBegin's player-name replacement. Cosmetics that are intentionally fixed must survive player accessory overrides. Use existing PreserveP1 fields where sufficient and final policy application where needed.
7. Choose random first player/seed once per new duel. Requests that fetch previews must not reroll active choices. Normal player-provided FirstPlayer overrides do not apply in this mode.
8. Normal non-balanced Solo, Custom Duel, replay viewing and room behavior remain unchanged. Developer CPU-vs-CPU testing must be a separate explicit path, unavailable through ordinary raw settings injection into balanced play.

Meaningful tests: reordered deck passes; changed finish passes; one extra powerful card fails; removed card fails; Main/Extra swap fails; unexpected side card fails; invalid/missing chapter fails; forged duelStarterData cannot alter fixed settings; completed chapter + CustomDuel.json cannot replace decks; IsMyDeck cannot replace decks; failed policy produces no active duel; ordinary campaign settings unchanged. Include two sequential matches to catch shared-template mutation.

Done: tests pass AND manually attempt edited-deck/custom-settings launches in-game. Valid prototype duels still finish normally.

## 11. Phase P4 — all characters and presentation

Files: remaining canonical deck records; Presentation.json; generated overlays; existing `YgoMaster/Data/ClientData/Images`, `SoloGateBackgrounds`, `SoloGateCards.txt`, `IDS`, `Text`; optional client files listed above.

Tasks:
1. Expand generator to 15 gates, 14 opponents each = 210 directed encounters. Opposite directions reuse canonical decks, not copied authored lists. Keep Yugi variants distinct.
2. Inventory existing artwork and record provenance/path/dimensions. Reference suitable existing images first. Add only needed assets under a unique balanced-mode prefix or subfolder accepted by actual loader.
3. Allocate gate thumbnails/backgrounds using the formats actually read by AssetHelper.Solo.cs and SoloGateCards.txt. Verify IDs/path behavior before generating. Do not assume arbitrary folders are automatically discovered.
4. Reuse SoloVisualNovel's inspected `ClientData/<baseDir>/dialog/<filename>` contract and a real working dialogue JSON sample. Record resolved baseDir in DECISIONS.md. Create portrait/name mappings matching that format; do not invent a new JSON schema without adding its parser.
5. Add short original intro/outro text per character, graceful skip, and no-dialogue fallback. Check both win and loss paths; do not promise distinct loss dialogue until actual loader supports it.
6. Validate every field/sleeve/music ID exists in this installation. Missing optional asset falls back to a known working default; missing deck or encounter must block launch.

Done: all 15 characters selectable; every directed encounter generated; smoke-test each character as player and CPU at least once. Portraits, names, text and music do not break launch. Game restarts without losing access.

## 12. Phase P5 — AI behavior, logging and balance

Files: DuelRunLogger.cs; Act_Duel.cs; NEW `YgoMaster/Data/BalancedCharacters/Logs/duels.jsonl`; PLAYTEST.csv; BalanceChanges.csv; optional NEW `Tools/BalancedCharacters/Summarize-Results.ps1`.

Log each launch and finish: schemaVersion, runId, game/mod version hashes, content revision, chapterId, playerCharacter, opponentCharacter, exact deck fingerprints, seed, firstPlayer, LP/hand/CPU config, control mode (human/CPU), start/end timestamps, result, finish reason, turns when available, test/normal flag. Use a server-generated runId. Do not label disconnect/crash/timeout as a gameplay loss. Append only one terminal result per run; link retries clearly. Exclude player identifiers not needed for balance.

AI capability checklist: Fusion/Polymerization; Ritual setup; Toon restrictions; equips; removal timing; Gravekeeper interactions; Exodia; situational traps. List actual relevant cards after P1. Capture a reproducible seed/replay and observation for failures. Configuration fields exist but their exact behavioral meaning is not verified; test values deliberately rather than assuming higher means smarter. Avoid AttackOnly and other tutorial flags in normal matches.

Testing schedule:
1. Three-deck prototype: six directed encounters, five seeded trials each, plus human play of each character. Diagnose card/AI failures before scale-up.
2. Fifteen decks: 105 unordered pairings x 20 games = 2100 games; ten starts per deck per pairing, with both deck sides exercised. Log who actually started, not just requested starter. Mark draws/stalls separately.
3. Verify developer CPU-vs-CPU path through MyType and OpponentType in the existing code before claiming automation. Headless simulation is NOT established. If unavailable, deliver a manual test queue and explicitly mark automated execution blocked; do not fabricate results.
4. Treat 20 games/pairing as screening, not proof. Compare pooled win rates and first-turn effects; replay outliers with human control because weak AI can make a strong deck look weak.
5. Preserve source-v1. Any adjustment creates balanced-v1, records rationale and affected pairings, and reruns those matchups. Preserve signature monsters and situational style. No automatic optimization toward modern tournament strength.

Done: each deck has a documented capability audit, actual run evidence, known limitations, and reviewed adjustments where needed. Do not set an arbitrary universal 50% per-matchup requirement; thematic decks can have natural favorable pairings.

## 13. Phase P6 — optional character campaign

Only after free duel works. NEW `YgoMaster/Data/BalancedCharacters/Campaign.json` defines encounter ordering, intro/outro references, unlocks and rewards. Generator maps it into separate campaign gates and IDs, distinct from free-duel gates.

Use existing Solo progression/reward code, scoped to allocated campaign IDs. Unlock opponents/presentation or alternate deck revisions without forcing grinding for the baseline fixed decks. Record exact defeat/retry/clear behavior. Test first clear, repeat clear (no unintended duplicate rewards), loss, restart, and upgrade from a prior mode revision. Do not reuse free-duel completion to grant campaign rewards.

Done: campaign path completes and persists, free duels remain available, original TCG campaign saves remain untouched.

## 14. Phase P7 — build, install, rollback and handoff

Files: Package-Mode.ps1, INSTALL.md, STATUS.md, NEW package manifest JSON.

Package only required binaries, canonical/compiled mode data, required assets, installer and documentation. Exclude development obj folders, crash dumps, user saves, downloaded game content, and unrelated copied image packs unless needed by existing runtime dependencies.

Manifest lists exact relative paths, SHA-256, size, required game/mod baseline, content version and deck revision. Installer validates target masterduel.exe location/version evidence, creates a NEW `YgoMaster-BalancedCharacters` runtime directory, and verifies launch/data path resolution. Do not assume renaming the mod directory works: inspect GameLauncher/settings path logic and test it. If it requires configuration, package explicit correct settings. Never overwrite LocalData, masterduel_Data or existing player directories.

Use dry-run output, a backup for any shared file that truly must change, and rollback instructions identifying created/changed files. If G cannot be written in the current session, provide the prepared installer and exact command; do not claim installation succeeded. Do not work around filesystem restrictions through another channel.

Acceptance: build and current campaign validation pass; balanced validator passes; clean install launches; one completed duel per player character; forged-input policy checks pass; normal TCG runtime still loads its own campaign/profile; rollback removes only installed mode files and preserves saves.

## 15. Required phase handoff format

At the end of each phase update STATUS.md with:
- Phase ID and status: NOT STARTED / IN PROGRESS / BLOCKED / COMPLETE.
- Files created/changed, with purpose.
- Exact build/test command, exit status, and evidence location.
- In-game checks actually performed, game version, and observed results.
- Open card mappings, runtime failures, unverified assumptions and next action.
- Source/runtime/package hashes when a build is shipped.

Do not mark an unchecked box complete to advance. Keep documentation aligned with final code, not abandoned approaches.

## 16. Copy-paste instruction for a future AI

> Read Balanced-Character-Duels-Implementation-Spec.md completely. Inspect the actual source at S and applicable AGENTS.md. Read Docs/BalancedCharacters/STATUS.md if it exists. Implement the next requested phase and its dependencies only. Preserve the immutable photographed deck baseline and original TCG saves. Distinguish existing hooks from proposed new files. Add explicit csproj compile entries as needed. Run the specified meaningful checks and report real evidence; never claim in-game success without running the game. If runtime access is blocked, continue independent data/code tasks and record the exact blocker. Update STATUS.md with files, commands, outcomes and the next action.

## 17. Initial task queue

- [ ] P0: baseline hashes/build/runtime check and isolated profile.
- [ ] P1: retrieve current transcription, verify photos, resolve all card IDs.
- [ ] P2: content compiler + three-character Solo overlay.
- [ ] P3: trusted launch policy + bypass/regression tests.
- [ ] P4: remaining 12 characters + character presentation.
- [ ] P5: actual AI competence tests and balance evidence.
- [ ] P6: optional campaign after free duel acceptance.
- [ ] P7: isolated install package, rollback and final handoff.

No phase implementation was performed while writing this specification.
