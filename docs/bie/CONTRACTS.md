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

## 5. The coverage record (work B of Navin's verdict, 29 October 2026)

Every review page says, by code, which lines of the book its video taught; the same facts are written next to the page.

- `<page>.coverage.json` (`bie.brain.coverage/1`, one record per video, `bie/brain/coverage.py: video_coverage`): `video_id`,
  `title`, `kind`, `status`, `assigned`, `covered`, `beats`, `beats_timed`, `rows` (one per assigned line: `item_id`, `page`,
  `kind`, `content`, `exam_importance`, `beats` with `beat_id`, `purpose`, `how`, `basis`, `scene`, `start_s`, `end_s`, `time`,
  `say`; `how`, `questions`, `questions_answered`, `covered`), `uncovered` (must be empty), `outside_beats`,
  `beats_beyond_scope`, `questions`, `questions_answered`, `basis` (counts of book / mixed / outside).
- The chapter page's `<page>.coverage.json` (`bie.brain.coverage.chapter/1`, `chapter_coverage`): `chapter`, `teachable`,
  `assigned`, `taught_by_a_passed_video`, `rows` (one per teachable line with its `videos`: `video_id`, `status`, `covered`),
  `unassigned` (must be empty), `videos` (per video: `status`, `assigned`, `covered`, `uncovered`, `beats`).
- Where the facts come from: the lines from the chapter map's concepts through `lesson.video_scope` (the scope the script
  was checked against); the beats and their `covers_item_ids`, `purpose`, `basis`, `answers` from the lesson plan; the times
  from the video spec's captions, one per beat, each carrying its `beat_id` (since 29 October 2026; an older spec is matched
  to the plans' beats in order, else by the caption's text). No AI call; Claude writes none of it by hand.
- These records are the "review record" the video path's formats lock (work D); a change bumps the schema version.

## 6. The video path's formats, locked (work D of Navin's verdict, 29 October 2026)

Every hand-over between two sections is one JSON file with a `schema` field `"<id>/<version>"` and one definition in
`bie/brain/formats.py`. A validator runs at every section boundary (`formats.accept` where a file is read, `formats.check`
where one is written): a value of the wrong shape stops the run with a `FormatError` naming the file, the format and the
field (`lesson_plan.json (bie.brain.lesson/3): $.videos[1].beats[2].basis: enum`). Unknown keys are allowed, so a file a newer
BIE wrote still reads; the keys named as required and the enums are the lock.

| Hand-over | Schema | File | Written by | Read by | Holds | Since |
| --- | --- | --- | --- | --- | --- | --- |
| chapter_map | `bie.brain.chapter-map/2` | `chapter_map.json` | Section 1 (bie/brain/understanding.py, run_chapter) | Section 2 lesson; Section 3c canvas; the game (Task 049); the notes (Task 050); the review pages | items keyed by item id (page, kind, content, teachable, teacher questions, unpack); map.concepts assign items to concepts | 2026-10-24 (/2: the unpack of Task 045d); locked 2026-10-29 |
| lesson_plan | `bie.brain.lesson/3` | `lesson_plan.json` | Section 2 (bie/brain/lesson.py, run_lesson) | Section 3c canvas; the game (Task 049); the notes (Task 050); the review pages (coverage) | plan.videos (concept_ids) and videos[].beats (say, covers_item_ids, answers, basis, source; audio reserved for the voice) | 2026-10-29 (/3: every beat carries source, S2-10; audio reserved for Task 047); earlier files are migrated |
| canvas_b_plan | `bie.brain.canvas-b-plan/1` | `plans/<part>.plan.json` | Section 3c, mode B (bie/brain/canvas_director.py) | bie/brain/canvas.py compile_plan; the review page | nodes with cues [beat_id, word]; the beats are the part's beats of the lesson plan | 2026-10-29 |
| world_c_plan | `bie.brain.world-c-plan/1` | `plans/<part>.plan.json` | Section 3c, mode C (bie/brain/canvas_director.py) | bie/brain/video/world.py compile_world; the review page | elements of a kit with cues; a camera path | 2026-10-29 |
| video_spec | `bie.video-spec/1` | `video_specs/<video>.json` | the compilers (bie/brain/canvas.py, bie/brain/video/world.py) through the canvas section | tools/render_spec.py (chunks, measure); bie/brain/video/render.py; the review page (captions → beat times) | scenes in part order; every caption carries its beat_id | 2026-10-29 (was bie.brain.canvas-plan/1; migrated) |
| canvas_summary | `bie.brain.canvas/1` | `canvas.json` | Section 3c (bie/brain/canvas_director.py) | the review page; the render workflow | one row per video with its parts (mode, status, seconds), the missing kits, the quality numbers | 2026-10-28 |
| render_cost | `bie.render.cost/1` | `cost.json` | tools/render_spec.py measure | summary; the review page | frames, minutes, machine minutes, rupees at the list price | 2026-10-29 |
| render_join | `bie.render.join/1` | `join.json` | tools/render_spec.py join | summary; the review page | the joined MP4 and the ≤ 720p review copy with their sizes | 2026-10-29 |
| render_summary | `bie.render-spec.summary/1` | `summary.json` | tools/render_spec.py summary | the review page | the run, the sha, the cost and the join | 2026-10-28 |
| review_record | `bie.brain.coverage/1` | `<page>.coverage.json` | tools/task046c_page.py (bie/brain/coverage.py video_coverage) | Navin; the game (Task 049); the notes (Task 050) | which book lines the video taught, by which beats, when and how | 2026-10-29 |
| chapter_review_record | `bie.brain.coverage.chapter/1` | `<page>.coverage.json` | tools/task046c_chapter_page.py (bie/brain/coverage.py chapter_coverage) | Navin | every teachable line → the video that teaches it | 2026-10-29 |
| visual_ideas | `bie.brain.visual-ideas/1` | `visual_ideas/<video>.json` | Section 3c, the visual-idea step (bie/brain/visual_thinking.py) | the dikhane-ki-list page (tools/task046d_ideas_page.py); the review page; Navin | per part its picture (type; decided by code from the book, by the card type, or by the maker) and per beat the idea, its relation, its nouns, what is seen and on which word; the relations outside the list; the needs | 2026-10-31 |
| needs | `bie.brain.needs/1` | `needs.json` | Section 3c (bie/brain/canvas_director.py) | the fetch step in GitHub Actions (tools/task046d_fetch_needs.py); Navin | the things no source had (thing, beats, kind, sources tried) and the capabilities BIE lacks (world kits, blocks) with the parts and beats that needed them | 2026-10-31 |

**Reserved for Task 047 (voice).** Every beat of the lesson plan may carry `audio` = `{"file", "duration", "words": [{"w",
"start", "end"}]}`, written by the voice section. `formats.voice_of(beats)` turns the beats that have it into the `voice`
that `bie/brain/video/timing.build` already reads, and both compilers (`canvas.compile_plan`, `world.compile_world`) pass it
when no voice is given, so the day the voice section writes the words, every cue lands on its real spoken word with no
change of format. Until then the timing comes from the text (130 words a minute, the danda pauses).

**What the game (Task 049) and the notes (Task 050) read** (`formats.READERS`; these fields never move without a version bump):

- **game (Task 049; bie/brain/game.py, game_build.py)** reads `chapter_map`: `items[*].item_id`, `items[*].content`, `items[*].content_type`, `items[*].teachable`, `items[*].teacher_understanding`; `lesson_plan`: `videos[*].video_id`, `videos[*].beats[*].covers_item_ids`, `videos[*].beats[*].say`; `review_record`: `rows[*].item_id`, `rows[*].beats[*].beat_id`, `rows[*].beats[*].time`.
- **notes (Task 050; bie/brain/notes.py)** reads `chapter_map`: `map.concepts[*].item_ids`, `items[*].kind`, `items[*].content`, `items[*].teacher_understanding`; `lesson_plan`: `videos[*].video_id`, `videos[*].title`, `videos[*].beats[*].say`, `videos[*].beats[*].covers_item_ids`, `videos[*].beats[*].source`; `review_record`: `rows[*].item_id`, `rows[*].how`, `outside_beats[*].beat_id`.

**The change rule.** A format changes only by (1) bumping its version in `formats.FORMATS`, (2) adding the migration step that
brings an older file up (`formats.MIGRATIONS`; a reader always migrates before it checks, so earlier run folders keep
working: `bie.brain.lesson/2` → `/3` adds `source` to every beat; `bie.brain.canvas-plan/1` and `bie.render-spec/1` are the
video spec under its old names), (3) re-checking `tests/fixtures/passed_outputs/` (`tests/test_task046c_formats.py` validates
the passed outputs after migration and fails the lane if a change breaks them), and (4) updating this section (the same
test checks that every format is named here at its current version). Never a hand edit of a run folder.

## 7. Dikhane ki soch (Task 046 Part D1, Navin's verdict of 30 October 2026)

Before any layout, the canvas section thinks about what the learner should SEE (`bie/brain/visual_thinking.py`):

- **The idea of every beat** (the maker's strict answer, checked by code): `idea`, `relation` (one of the ids of
  `bie/brain/rulebook/visual_verbs.json`: reject, accept, compulsory, limit, more_less, count, sequence, cause_effect, compare,
  part_whole, place, change, promise, question; or `other` with a note, logged in `relations_outside_list` so Navin can add an
  entry), `things`, `people`, `places` (the nouns a picture can show; a real person is never drawn, card rule 8), `shows` (what is
  seen, a few words, never a sentence), `on_word` (the word of the beat the picture appears on).
- **The picture of a part, decided by code first** (`picture_of`): a book diagram or table the part covers (the chapter map's items
  of kind `diagram` / `table` and their `diagram_label` / `table_row` children) is drawn as itself: a timeline with the book's years
  and labels (`timeline_build`), a table row by row, a panel of items as a gallery of icon cards (icon + name), a flow of boxes and
  arrows (`flow_build`); code places the node (`picture_node`, kind `picture` in `bie/brain/canvas.py`) and the maker builds around
  it. With no book picture the card part's type is the hint; the maker decides only where code cannot.
- **The needs list** (`resolve_needs`): the nouns are searched in the full icon index (`bie/toolbox/icons.py`: aliases, Hindi words,
  emoji names; religious symbols only when asked for) and in the lesson's asset library; a noun found nowhere is a need.
- **The record**: `visual_ideas/<video>.json` (`bie.brain.visual-ideas/1`) is the dikhane ki list (beat → what is seen → on which
  word → how); `needs.json` (`bie.brain.needs/1`) the needs and the missing capabilities (world kits, blocks) with the parts and
  beats that needed them. `canvas.json` rows carry a `report` (distinct icons, text-only screen seconds and share, picture types,
  worlds, book pictures drawn, relations outside the list) and `quality` the chapter totals.
- **The checks** (`canvas_director.check_plan`): D1-01 every beat shows a non-text thing cued on its words; D1-02 no text-only
  screen over 10 s; D1-03 screen text a name or a short phrase (8 words; a board 2 lines of 28 characters), never a sentence;
  D1-04 every book picture the part covers is drawn; D1-05 a world only for the example's story at the example's place, and the
  same kit never in two consecutive parts; D1-06 a caution or fact-check line never on screen.
