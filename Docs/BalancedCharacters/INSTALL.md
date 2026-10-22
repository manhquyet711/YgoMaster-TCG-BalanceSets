# Balanced Characters 0.2.1 - development prototype

For the existing inspected v5 installation, use Install.cmd from the 0.2.1
upgrade package. It updates the server, client and additive chapter overlay,
preserves settings/decks/saves, and includes the balanced settings editor.
The initial installer described below is for a new runtime folder only.

Each gate now has a battle followed by a separate connected Goal. Select
the battle to open deck and Play controls. The new graph still needs
in-game verification; previous one-node map failures are documented in
NATIVE-MAP-0.2.1.md.

This build adds two fixed-deck free-duel gates to SOLO > Stories:

- Balanced Characters - Kaiba: play Kaiba against Joey.
- Balanced Characters - Joey: play Joey against Kaiba.

Each deck has 40 Main and 3 Fusion/Extra cards, transcribed and reviewed from the user's photos. Duels use 8000 LP, five opening cards, normal shuffle, modern engine effects, and CPU setting 97. Card ownership/crafting is not required for the supplied loaner decks. No free-duel gem/card rewards are granted. A win records chapter completion; replay remains available.

## Installation

1. Extract the ZIP. Close Master Duel before testing.
2. Run Install.cmd. It uses the existing YgoMaster-TCG-Updated-2.8.0 installation as its asset/data base and creates a NEW YgoMaster-BalancedCharacters folder beside masterduel.exe. It refuses an existing target to preserve possible saves. The original TCG installation is not changed.
3. Open YgoMaster-BalancedCharacters and run Start-Balanced.cmd.
4. Open SOLO > Stories. Look for Balanced Characters - Kaiba / Joey. Pick a character gate, inspect both recipes, and launch its duel.

For a non-default game path, run Install-Prototype.ps1 -GameRoot followed by the quoted game directory. -DryRun validates the package and selected game without writing files. The installer checks the inspected GameAssembly hash; a changed game needs revalidation.

The package reuses the existing TCG assets, so it is small and is NOT a standalone game. Its manifest verifies shipped files, not the integrity of all downloaded/base assets.

The Source folder is a code/data checkpoint without the original game's assets. For development outside the existing project, restore base mod Data into Source/YgoMaster/Data, then copy Payload over Source/YgoMaster before running Build-Balanced.ps1 -CompilePrototype. Payload contains the unchanged native loader required by the build. Do not copy personal save/deck folders into a test checkout.

## Separate profile and launcher

Server and client data use this new folder's Data directory. Local progress is stored under Data/Players/Local. Existing player saves/decks are not imported. Ports 5099 (HTTP) and 5098 (session) are reserved for this prototype. Its launcher starts the correct server explicitly, checks readiness, and launches the client from the correct directory. Server output goes to LaunchLogs.

Close the game normally. Stop-Balanced.ps1 stops only the YgoMaster.exe whose path belongs to this installation when you finish testing. No original TCG process is terminated by that script.

## What has been verified

Compilation; original campaign data; canonical-deck validation; actual server request handlers including edited-deck/custom-settings bypass attempts; ordinary custom-duel regression; independent deck copies. These are offline handler tests, not an engine simulation.

## What still needs testing

No in-game acceptance is claimed. Verify that both gates appear, recipes show the correct decks, each duel starts/finishes, and a win/restart preserves completion. The prior Stories thumbnail compatibility candidate is included along with loading of this mode's separate thumbnail file; its in-game effect remains unverified. If FILE LOAD ERROR persists, keep SoloThumbnailFix.log and LaunchLogs.

Yugi remains blocked by unresolved Spellbinding Circle mapping. The other twelve transcriptions are retained but are not selectable until reviewed and resolved. No substitute cards or balance changes were introduced.

## Rollback

Close the game, stop this prototype's server, and use the original mod launcher. The prototype is isolated in YgoMaster-BalancedCharacters; retain Data/Players if you want its progress before removing that folder manually.
