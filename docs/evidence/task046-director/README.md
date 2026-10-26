# Task 046 Part A · the code director's offline proof on v3

Made on 26 October 2026 by `python -B tools/shot_list.py --from-run <run> --videos v3 --out <dir>` on the run folders named in
`tests/fixtures/task046/v3_tissue.json` (no AI call, Rs 0). Files:

- `shots/v3.json`: the shot list (schema bie.brain.shots/1): one shot per spoken clause with its seconds, block(s), capability,
  visual level, camera, labels, caption, assets, the per-level split, the checks and the 24-rule table.
- `SHOTS.md`: the same, readable.
- `shots.json`: the run summary.
- `W01.md`: every W-01 hit (the five beats of v3 that point at the book) with the sentences before the wording patch.

Status: IMPLEMENTED (checked offline and by tests/test_task046_shots.py). Nothing is rendered yet (Part B) and nothing is ACCEPTED.
