# Task 046 Part B · benchmark render of v3's epithelium family segment

Run 40298550697 from 1ffc2a09; script from https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/vm-t046-v3-wording-patch-resume-brain-lesson. Status: IMPLEMENTED (nothing ACCEPTED until Navin's verdict).

| route | shots | seconds | main level | one change every | rules pass / partial / fail | render s per video s | machine min | Rs at list price |
|---|---|---|---|---|---|---|---|---|
| A | 77 | 337.63 | L5a | 4.59 s | 14 / 2 / 2 | 27.24 | 153.3 | 103.02 |
| C | 77 | 337.63 | L5a | 4.59 s | 15 / 2 / 1 | 30.06 | 169.1 | 113.65 |

Bridge (real Remotion, first 10.0 s of route A): 37.54 render s per video s (bundling included), frames against the preview path differ by [0.0, 0.0, 0.0] (mean grey levels, < 8 passes): passed.

Per route: review-720p.mp4 (the video), REPORT.md, RULES.md (24 rules with frame numbers), SHOTS.md (shot by shot), cost.json, contact-*.png.
