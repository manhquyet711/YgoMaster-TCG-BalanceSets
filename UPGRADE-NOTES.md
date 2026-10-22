# TCG campaign compatibility update

Target: Master Duel **2.8.0**, Unity **6000.0.61f1**.

Updated source: pixeltris/YgoMaster v1.79, commit c24aa153f78c72006e904174043b1c0c553680da, with the supplied June 30, 2025 TCG campaign merged into it.

## Changes

- Updated game hooks, IL2CPP bindings, duel bindings, and settings to the v1.79 compatibility baseline. The original 2.3.0 version string was not used as a substitute for a compatibility update.
- Retained the TCG campaign, custom artwork, text, shop, historical regulations, rewards, and progression settings.
- Retained 6,833 custom card rarity overrides while extending the catalog to 13,997 entries. Card catalog counts are not a guarantee that every card can be acquired or used by this particular game installation.
- Preserved custom pack descriptions, player name, CPU difficulty, and icon. Used the newer upstream progression implementation, which contains the corresponding rarity fixes and additional compatibility handling.
- Kept the newer dismantle implementation instead of restoring the old mod's loop that never removes processed cards.
- Updated multiplayer offsets to 15616 and 15512; multiplayer remains disabled by default.
- Fixed a surplus quote in the High-Speed Riders shop entry, 65 empty regulation-list entries, and leading-zero BGM numbers. No missing card IDs were guessed.
- Included the unchanged official v1.79 native loader and modern card-data files from the locally supplied official release ZIP. The C# executables were rebuilt from this updated source.

## Build

Run `Build-Updated.cmd`, or run `Build-Updated.ps1 -Validate` in PowerShell. Requires the .NET Framework 4.8 developer tools. Visual Studio MSBuild is detected automatically.

The native loader has no source differences between upstream v1.61 and v1.79; it does not need rebuilding for this update. The optional C++ SettingsEditor source is retained, but its executable was not built on this machine because the Visual C++ compiler is not installed.

## Validation and limits

Both Release/x64 C# projects compile. JSON validation and the real compiled server's data initialization are checked separately. `Tools/ValidateCampaign.cs` initializes the server without starting network listeners, then verifies catalog size, campaign chapters and duels, shop packs, progression settings, offsets, and a custom rarity.

A full server launch reaches the HTTP-listener stage, where the managed execution environment reports `PlatformNotSupportedException` for `System.Net.HttpListener`. In-game startup, artwork rendering, duels, and reward progression have therefore **not** been verified. The game's Unity version and duel.dll size match the newer baseline, but the game's reported application version still needs checking at launch.

## Installation

The companion update package contains changed/new source files and the rebuilt runtime. Its installer checks original file hashes before updating the supplied source project, backs up overwritten files, and creates a separate runnable `YgoMaster-TCG-Updated-2.8.0` folder directly inside the game folder. It does not modify the other mod folders or the game's executable/DLLs. Existing player saves are not migrated automatically.

After installation launch `YgoMaster-TCG-Updated-2.8.0\YgoMasterClient.exe`. Check the home screen, deck editor, an early campaign duel, its rewards, shop unlocks, and a later campaign duel before migrating your progress.
