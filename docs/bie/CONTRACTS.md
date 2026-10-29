# BIE records and contracts

What every BIE run writes, where it lives, and how a locked item points back to the run that made it. Navin, 29 October
2026: "Jo cheejen BIE tayar kar rha hai wo to sabhi cheejen iske record mein honi hi chahiye tabhi to seekhega aur cheejen
khud ke paas hone se AI par nirbharta kam hogi." Everything BIE makes stays in its run records; nothing is deleted
(CLAUDE.md, "Preserve history and evidence").

## 1. Run folders (`blindtest-results:runs/<run id>/`)

A VM job `jobs/<id>.json` on the `codex-jobs` branch runs one section of `tools/run_brain.py` on the VM and publishes
its folder as `runs/vm-<id>-brain-<section>/`; a CI render publishes `runs/<dest>/`. Every folder holds:

| File | What it is |
| --- | --- |
| `SUMMARY.json` | status, stop reason, the section's `quality` block, `cost` (ledger estimate, cap, subscription calls), `estimate`, `level`, the fake flag |
| `LEDGER.jsonl` | one line per AI call: section, unit, round, route, model, tokens, cost, cache hit |
| `RUN_LOG.txt` | the run's log |
| `records/<section>--<unit>.json` | the process record of one step: the card, the prefix and review-prefix hashes, the inputs digest, every round (maker call meta, the output, code problems, the review, the patch), `navin_verdict` |

Per section, the outputs the next section reads:

| Section | Outputs | Readable page |
| --- | --- | --- |
| understand (Section 1) | `chapter_map.json` (pages, `items` keyed `p<page>-i<n>` with `unpack` and `unpack.real_world_example`, the map, `quality`), `naksha.json` | `MAP.md`, `PAGES.md` |
| lesson (Section 2) | `lesson_plan.json` (the plan, every video's beats, notes, `real_world`, `checks`, `record`) | `SCRIPT.md`, `scripts/v<n>.md` |
| canvas (Section 3c) | `canvas.json` (per part: mode, place, story, rounds, first try, level, seconds), `plans/<part>.plan.json`, `video_specs/v<n>.json`, `assets/` | `CANVAS.md` |
| render (CI, `BIE Task046c Render`) | `summary.json`, `cost.json`, `join.json`, `video_spec.json`, `review-720p.mp4` (the full MP4 is the run's artifact) | `REPORT.md` |
| image (VM) | `SUMMARY.json` with one row per image (status, source `bie_chatgpt_plan`, `generated_by`, `prompt`, `generated_on`), `images/` | `IMAGES.md` |

The job's result (`jobs/<id>.result.json` on `codex-jobs`) names the folder, the minutes, the rupees and the plan usage.

## 2. The library and its pointers (`bie/brain/rulebook/explanations.json`)

Only Navin's verdict locks (the lock tool `tools/lock_explanations.py`, run after his yes on named items, in a reviewed
PR). Every locked entry carries:

- `from_run`: `<run id>:<item id>`, the run folder on `blindtest-results` and the key of `chapter_map.json` → `items`;
  the step that made it is `records/understand--page-<page>.json` of that folder (the item's `page` field names the
  page) and its calls are the `LEDGER.jsonl` lines of that unit;
- `source`: who locked it and when (`Navin, 29 October 2026`);
- `locked_version`: the library version written at the lock (examples), so a later change is told apart;
- `status`: `locked`.

Two kinds of entries:

- `entries`: a term's plain meaning, everyday image, why chain and analogy (Task 045d), reused as the unpack and spoken
  by the script maker as the opening;
- `examples` (Navin, 29 October 2026): a concept's real-world example (place, actors, goods, numbers before → after,
  steps with their mechanism links, the sentence that names the term after the story, the real-life link), filed under
  the item's first unpack term with the other terms as aliases. `narration` and `narration_locked` hold the spoken
  wording once the narration work has made it natural; until then they are `null` / `false` and the maker speaks the
  locked facts in its own words.

## 3. Library first (the contract of Section 1 since 29 October 2026)

For a chapter of a subject family whose items carry a real-world example (today: economics), the page step reads the
library before the AI: the locked examples whose term appears in the page text are shown to the maker as given, and
after the maker's answer code fills `unpack.real_world_example` of every item whose own unpack terms name a locked
example (the maker's version is replaced; an item that only mentions the term in passing keeps its own), marking
`example_source` `library:<key>`; an example the maker wrote is marked `ai`. `MAP.md` and `SUMMARY.json → quality`
count `real_world_from_library` against `real_world_from_ai`. The S1-16 checks run on the filled item as on any other.

## 4. Where the decisions live

- `docs/roadmap/ROADMAP.md` (Task 046) and `docs/roadmap/STATUS.md`: Navin's decisions in his words, dated.
- `bie/toolbox/licence_policy.json`: every licence verdict (sources approved by name with the date and his words, the
  India boundary's condition, software decisions, generated images and their provenance fields).
- `bie/brain/rulebook/*.json`: the rules and the library, versioned, each change listed in the file.
