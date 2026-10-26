# Task 046 Part B · benchmark render of v3's epithelium family segment (26 October 2026)

Run 40298550697 of `.github/workflows/task046-benchmark.yml` on PR #75 (commit `48adca67`), script from
`blindtest-results:runs/vm-t046-v3-wording-patch-resume-brain-lesson` (v3 passed, the five W-01 beats rewritten). The videos
and the contact sheets are on the `blindtest-results` branch under `runs/t046-v3-benchmark/` (`A/review-720p.mp4`,
`C/review-720p.mp4`, `A/contact-*.png`, `C/contact-*.png`, `bridge/bridge_sheet.png`); this folder keeps the text files of
that run as evidence. Status: IMPLEMENTED (nothing ACCEPTED until Navin's verdict).

| file | what |
| --- | --- |
| `REPORT.md`, `summary.json` | both routes side by side and the bridge |
| `RULES-A.md`, `RULES-C.md` | the 24-rule table per route, with the first failing frame |
| `SHOTS-A.md`, `SHOTS-C.md` | the shot list, frame ranges, levels, cameras, labels, sentences |
| `cost-A.json`, `cost-C.json` | render seconds per second of video, machine minutes, USD and ₹ at the list price, per chunk |
| `bridge.json` | the real-Remotion sample against the preview path |
| `models.json` | the Blender sheets of route C (cells, hairs, seconds, bytes per member) |

The numbers in one line: 77 shots, 337.6 s, L5a 93.6 %, one visual change every 4.59 s; route A 27.2 render seconds per
second of video (153.3 machine minutes, ₹103 at the list price, billed ₹0), route C 30.1 (169.1 minutes, ₹114); rules A
14 pass / 2 partial / 2 fail (B-10, B-03), C 15 / 2 / 1 (B-10); the real-Remotion sample gives the same frames (mean
difference 0.0) at 37.5 s per s with bundling against 20.8 on the preview path.
