# Balanced Character Duels — development project

Source: F:\ChatGPT\Balanced-Character-Duels. Installed game runtime remains
G:\Game\yugioh online\copy of master dual\Yu-Gi-Oh!  Master Duel\YgoMaster-BalancedCharacters.

Version 0.2.2 implements 14 photo-reviewed character decks and 182 fixed-deck
Solo encounters. Original Yugi is blocked by missing Spellbinding Circle;
Yugi (Battle City) is included. No balance substitutions have been made.

Run .\Build-Balanced.ps1 -CompilePrototype to build and run content, policy and
server-handler checks. Python 3.9+, .NET Framework and MSBuild are required.
This source directory is not a standalone playable game installation.

Use the 0.2.2 upgrade package on the existing 0.2.1 runtime. It preserves the
working client, settings editor, settings, ports, saves and old Kaiba/Joey decks.
Do not rerun the older 0.2.1 installer over 0.2.2.

Read Docs/BalancedCharacters/STATUS.md, RELEASE-0.2.2.md and DECISIONS.md for
actual completion and outstanding gameplay checks. Build/handler success does
not establish game rendering, AI competence or deck balance. The upstream
README.md describes the base mod.
