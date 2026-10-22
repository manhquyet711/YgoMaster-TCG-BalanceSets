# Decisions and corrections

## 0.2.2 roster and map expansion (2026-10-22)

- All twelve remaining photos were compared visually against the supplied transcriptions; reviewed source records contain photo SHA-256 and review date. See PHOTO-REVIEW-0.2.2.json.
- Corrections, with original quantities preserved: Mako's **Giant Turtle Who Feeds on Flames**; Keith's **Bokoichi the Freightening Car**; Gravekeepers' **Charm of Shabti**; Jaden's final Fusion pairs **Thunder Giant**, **Wildedge**, **Wild Wingman**, **Rampart Blaster**. These correct transcription errors and are not balance changes.
- Slifer, Ra and Limiter Removal select their original card IDs using explicit local passcode mappings. **Marie the Fallen One** maps to the renamed **Darklord Marie**, confirmed by Konami's official database: https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=5209&ope=2
- Fourteen decks are fully reviewed/resolved. Original Yugi remains blocked because Spellbinding Circle is absent from the installed tables and passcode map. Yugi (Battle City) is available. Published Kaiba/Joey fingerprints are unchanged.
- The compiler/loader support 2..15 verified characters, with stable gate and opponent chapter IDs. Each gate uses a connected chain of opponent battles and one separate terminal Goal, preserving the native graph requirement. All battles have OPEN status from entry; the Goal requires all battles in its gate complete. Disconnected maps/cycles fail before any merge.
- The working 0.2.1 client is retained. This release changes server/content only; existing card illustrations and default duel presentation remain in use. No guessed portrait, BGM or dialogue IDs are introduced.
- Runtime evidence contains client-reported human-vs-CPU runs, not automated AI-vs-AI trials. Configured first player is recorded separately from observed first player (unknown). Logs omit account codes and player names. No balance changes have been made.
- Game-dependent P5 screening, optional P6 campaign and new portraits/dialogue remain pending. The manual screening queue has 91 pairs x 20 games = 1,820 pending games; it is a test plan, not results.

## Authoritative project paths

New development source S = `F:\ChatGPT\Balanced-Character-Duels`.
The original specification's upstream source path is now the read-only reference baseline, not the target for further changes.

## Confirmed photograph corrections (2026-10-21)

- Kaiba: two Blizzard Dragon cards replace the uncertain split normal-dragon transcription. Corrected Main total is **40**, Extra total 3. The old 41 total counted a malformed continuation bullet as a card. This correction supersedes the original specification roster count; no balancing substitution was made.
- Yugi: **Red Archery Girl**, not Rude Kaiser, appears in the photographed list. Main remains 40. Preserve the original markdown for provenance; corrected SourceDecks/yugi.json is the reviewed source.
- Joey: pictured Main 40, Extra 3; source reviewed with no quantity corrections.

## ID choices

Some cards have multiple identical English names in the bundled tables. Aliases.json explicitly selects original-card IDs using local YdkIds.txt passcode mappings. No generic lowest-ID or first-match rule is used. These mappings identify data entries, not historical effects or AI capability.

Red-Eyes B. Dragon is an explicit historical-name alias to Red-Eyes Black Dragon. Spellbinding Circle remains unresolved; do not substitute a different trap. Other transcriptions with [CHECK] remain blocked even if a partial name resembles an available card.

## 0.2.0 implementation decisions (supersedes foundation limits below)

- Build the next vertical slice with the two ready decks, Kaiba and Joey, rather than wait for Yugi's unresolved card. No replacement card is permitted. Explicit activeCharacterIds controls compilation; unavailable characters are not silently skipped.
- Reserve gates for all fifteen stable roster IDs, but publish only the selected two. Allocations persist in Ids.json and are checked against the original campaign and thumbnail entries.
- Merge the generated Solo overlay in memory; preserve original Solo.json. Load generated thumbnail mappings from a separate optional file.
- Fixed-deck launch enforcement now applies at real server handlers. Card ownership is bypassed only through supplied rental decks. Free duels grant no card/gem rewards.
- Enable this development slice in its own runtime/profile, using ports 5099/5098 and an explicit server launcher. No in-game acceptance is claimed.

## Historical foundation implementation limits

- Balanced mode disabled; Mode.json not yet loaded by runtime code.
- FixedDeckPolicy is a tested helper, not active launch enforcement.
- Build-Content generates candidate payloads only after all three reviewed decks resolve; no runtime gate metadata is generated yet.
- No historic-rule emulation, AI code changes, multiplayer work, campaign progression or balancing changes have been made.
- No personal save data copied. No game launch attempted while the copied game's downloaded content is missing.
