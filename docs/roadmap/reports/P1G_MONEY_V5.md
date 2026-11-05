# Money v5 through the box rule (5 November 2026) — STOPPED for Navin's verdict

Navin, 5 November 2026: "Isi chapter ka Money v5; lakshya overlap 36 s se kam, lamba wala 0; v2 ke saath numbers."

**What ran (all BIE, ₹0 AI):** VM job `p1g-money-showplan-v5-a` (Codex maker, max_rounds 6) wrote the scene plan of
Money v5, "Gold link टूटा, फिर भी Dollar की माँग क्यों रही?" (45 beats from lesson-f), checked only by the compiler with
the box rule of PR #149: passed in 5 rounds, 8 scenes, 211 elements, 540 s (run folder
`runs/vm-p1g-money-showplan-v5-a-brain-showplan`). Compiler problems per round: 75 → 5 → 1 → 3 → 0 (round 1 showed
40, spread over every scene, and counted the other 35 per scene). The one button (BIE P1 One Button, dest
`p1g-money-v5`) rendered it in 6 chunks: 16,206 frames, 4.5 min wall, ₹17.11 at list price, ₹0 billed; the text-audit
gate passed, so the review copy was published (`runs/p1g-money-v5-v5`, page `runs/p1g-money-v5/REVIEW.html`). A local
audit with main's code before the render gave the same numbers.

| | BIE Money v5 (box rule) | BIE Money v4 (4 Nov) | Claude's v2 demo (not BIE output) |
| --- | --- | --- | --- |
| Length | 9.0 min | 14.7 min | 10.9 min |
| Texts seen on screen | 204 | 338 | 320 |
| Overlap seconds in all | **3** | 472 | 36 |
| Overlap seconds per minute | 0.3 | 32.2 | 3.3 |
| Longest overlap | **1 s** | 61 s | 9 s |
| Overlaps held over 2 s | **0** | 23 | 4 |
| Texts under 36 px | **0** | 65 | 32 |
| Text-audit gate | passed | would fail | would fail |

Both targets met: overlap seconds under 36 (3), no overlap over 2 s (0).

**Honest notes.** The 3 remaining overlaps are one sample each: two labels near each other at 206 s, a new label
popping in while the old one fades at 278 s, two "$" signs at 535 s. v5 is shorter and carries fewer texts than v2,
hence the per-minute row. The audit measures text on text only; text on things, faces, background zones and the frame
edge are refused by the compiler before the render, and an eye check of 18 stills (one every 30 s) found labels
beside things and faces clear, with two label pills only touching an edge (the Triffin label near the vault, the
"निर्यात भुगतान" label). Screen labels are Hindi; the subtitles follow the Hinglish narration. Status: the box rule is
IMPLEMENTED and now INTEGRATED on a real chapter video; nothing is ACCEPTED until Navin's verdict. Captions only; the
voice waits on his yes.

Decision page: https://claude.ai/artifact/FLK6Nd7iF856J1UERffcPA
