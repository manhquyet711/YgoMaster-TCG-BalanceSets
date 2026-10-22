# Why the balanced chapter had no battle controls

Inspected installed Master Duel 2.8.0 GameAssembly.dll, SHA256
CA24A284A86DC394F6B0CBEAAD455D29E5F6B95FC8DB8FC42812B29DE3C7620C.

The running v4 log confirms configured IDs 20180004 and 20190003, and
Chapter.SetData is reached. Its dialog type was already 0 before our v4
override. No balanced Click or Opening deck/Play panel entry was recorded.
The earlier tutorial-only explanation did not account for the node class.

Targeted Ghidra analysis with automatic analysis disabled recovered this
ordering in ChapterMap.InitChapter (VA 0x1808b16e0):

1. Read the chapter's deck/NPC/scenario settings.
2. Call ClientWorkUtil.GetSoloGateClearChapter (VA 0x180647e90).
3. If the current chapter ID equals that clear chapter, construct ChapterGoal
   using its constructor at VA 0x1808c4a50. This happens before battle versus
   practice classification.
4. Otherwise select a chapter subclass according to the chapter settings.
   Loaner-only practice construction calls ChapterPractice's constructor at
   VA 0x1808c59e0.
5. Call the created object's SetData and register it in chapterDataDic.

The balanced overlay marks each gate's only battle as clear_chapter:
2018 -> 20180004 and 2019 -> 20190003. Therefore both pass step 3 and create
ChapterGoal. A later edit to dType does not replace that object or its UI.
That explains why v4's dialog-type adjustment alone was ineffective.

Addresses were recovered from the Assembly-CSharp.dll code-generation
module and metadata method tokens, then checked against the native code.
The supplied decompilation excerpt preserves the underlying evidence.

v5 intercepts GetSoloGateClearChapter only on the current thread while
ChapterMap.InitChapter is constructing a configured balanced battle. If
the returned clear chapter is that same battle, the hook returns 0 for
that single comparison. The scope is restored in finally. Other calls,
other chapters and the server's completion configuration remain unchanged.
The existing balanced dialog override then selects the deck/Play panel for
the battle object. This still needs an in-game acceptance test.

Validation: C# build, 48 content/policy/handler checks, native metadata
signature/enum validation, and installer fixture checks. These do not
execute the native UI hooks. Expected runtime evidence is:
Building playable chapter, Bypassed goal-node construction, a chapter Click,
and Opening deck/Play panel, all in SoloThumbnailFix.log.
