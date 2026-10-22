# Connected chapter map in 0.2.1

This supersedes the earlier v4/v5 explanations. The v5 runtime log confirms
the goal override ran for both battles, but no Click or panel-open event.

Further targeted analysis of installed GameAssembly.dll found that
ChapterMap.CreateNodeMap (VA 0x1808af240) needs both a root and a connected
ChapterGoal. It finds the root through parentID == 0. It records the goal
while linking chapters with nonzero parents, then indexes the chapter-node
dictionary using that goal object. A single root goal does not populate
that goal reference; suppressing the only goal in v5 also cannot populate it.
The missing connected goal is therefore a structural map defect.

ChapterMap.Create (VA 0x1808afad0) calls this map builder before cloning and
wiring the visible chapter buttons. A failure there explains the unchanged
template screen and lack of chapter-click logs. These are static findings;
in-game acceptance of the new graph remains required.

0.2.1 emits:

| Gate | Root battle (unchanged) | Goal | Goal parent |
| --- | --- | --- | --- |
| 2018 / Kaiba | 20180004 | 20189000 | 20180004 |
| 2019 / Joey | 20190003 | 20199000 | 20190003 |

Each gate's clear_chapter now points to its separate goal. Goal nodes have
no NPC, scenario, unlock, or reward set. The loader validates exactly one
battle and one connected terminal goal per prototype gate before committing
any content. The current prototype is explicitly limited to two reviewed
characters; expanding the roster needs an intentional map design.

The server rejects premature goal completion and rejects launching a goal
as a forged custom duel. A win completes the battle, after which its goal
can complete without rewards or a duel. Existing battle IDs, exact decks,
rules and card fingerprints are preserved.

The client removes the v4 dialog mutation and v5 goal-lookup override.
Remaining chapter hooks only report native construction, map-ready objects,
clicks and panel opens. Expected map-ready types are ChapterPractice for
the battle and ChapterGoal for the goal, with non-null game objects.

Evidence was obtained from the user's installed 2.8.0 GameAssembly.dll,
SHA256 CA24A284A86DC394F6B0CBEAAD455D29E5F6B95FC8DB8FC42812B29DE3C7620C,
using its IL2CPP metadata/code-generation module and targeted Ghidra scripts.
