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
| render (CI, `BIE Task046c Render`) | `summary.json` (with the text check and the respec counts, Task 048), `cost.json`, `join.json`, `video_spec.json`, `audit.json` (the text check of every sampled frame), `RESPEC.json` (when the plans were compiled again), `review-720p.mp4` (the full MP4 is the run's artifact) | `REPORT.md` |
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
| show_spec | `bie.show-spec/1` | `video_specs/<video>.json` | the showing engine's builders (bie/brain/gold/*, the scene-plan compiler of Phase 1) | bie/brain/video/engine (the renderer); tools/render_spec.py; the render workflow | scenes in seconds with the engine's elements and camera keys; subtitles from the voice timeline; the asset name to served path map | 2026-11-03 |
| canvas_summary | `bie.brain.canvas/1` | `canvas.json` | Section 3c (bie/brain/canvas_director.py) | the review page; the render workflow | one row per video with its parts (mode, status, seconds), the missing kits, the quality numbers | 2026-10-28 |
| render_cost | `bie.render.cost/1` | `cost.json` | tools/render_spec.py measure | summary; the review page | frames, minutes, machine minutes, rupees at the list price | 2026-10-29 |
| render_join | `bie.render.join/1` | `join.json` | tools/render_spec.py join | summary; the review page | the joined MP4 and the ≤ 720p review copy with their sizes | 2026-10-29 |
| render_summary | `bie.render-spec.summary/1` | `summary.json` | tools/render_spec.py summary | the review page | the run, the sha, the cost and the join | 2026-10-28 |
| review_record | `bie.brain.coverage/1` | `<page>.coverage.json` | tools/task046c_page.py (bie/brain/coverage.py video_coverage) | Navin; the game (Task 049); the notes (Task 050) | which book lines the video taught, by which beats, when and how | 2026-10-29 |
| chapter_review_record | `bie.brain.coverage.chapter/1` | `<page>.coverage.json` | tools/task046c_chapter_page.py (bie/brain/coverage.py chapter_coverage) | Navin | every teachable line → the video that teaches it | 2026-10-29 |
| visual_ideas | `bie.brain.visual-ideas/1` | `visual_ideas/<video>.json` | Section 3c, the visual-idea step (bie/brain/visual_thinking.py) | the dikhane-ki-list page (tools/task046d_ideas_page.py); the review page; Navin | per part its picture (type; decided by code from the book, by the card type, or by the maker) and per beat the idea, its relation, its nouns, what is seen and on which word; the relations outside the list; the needs | 2026-10-31 |
| needs | `bie.brain.needs/1` | `needs.json` | Section 3c (bie/brain/canvas_director.py) | the fetch step in GitHub Actions (tools/task046d_fetch_needs.py); Navin | the things no source had (thing, beats, kind, sources tried) and the capabilities BIE lacks (world kits, blocks) with the parts and beats that needed them | 2026-10-31 |
| coder_made | `bie.brain.coder-made/1` | `made.json` | the coder section (bie/brain/coder.py) | the fetch step in GitHub Actions (tools/task046d_fetch_needs.py --made); Navin | the drawings BIE's coder made for the needs no source had: per thing its file, hash, tags, licence and provenance (who drew it, the spec, the date), and the needs it did not draw with the reason | 2026-11-02 |
| notes_page | `bie.notes-page/1` | `notes/pages/<page>.json` | BIE's AI from the chapter's question list (part C) | bie/brain/notes_pages.py (problems; still_spec: a picture page → a show-spec still the engine draws; deck_of: pages → the existing notes deck); bie/brain/notes_render.py (render_notes_html; print view is the PDF); the review page | one question per page, answered by a picture (the same saanche as the video), a flow, a comparison or a table, with the book items it answers from | 2026-11-03 |
| game_level | `bie.game-level/1` | `game/levels/<level>.json` | BIE's AI from the chapter's stories (part C; agreement decision 6: a video's story becomes a level) | bie/brain/game_levels.py (problems, stage_of: a level → one stage of the phone runtime); bie/brain/game_runtime.py (render_game_html plays it); the review page | one of eight mechanics: five drag ones (run_process, place_right, build_timeline, find_partner, cause_effect) with pieces, places, what each right move does and each wrong move breaks; act_as (role, situation, choices on the branch engine) and predict (a slider on the slider engine), added 2026-11-04 from the economy reference videos; allocate (split a total among 2-5 boxes, each with its sound range and what goes wrong too low or too high; the allocate engine), added the same day; optionally a `world` (an economy world of the showing engine with its saancha parameters) whose `spot`s carry the places, drawn by the runtime with the videos' code (2026-11-04); and the book items played | 2026-11-03 |
| scene_plan | `bie.scene-plan/1` | `plans/<video>.plan.json` | BIE's director (part C; the Money v2 gold plan is Claude's demo example) | bie/brain/video/showplan.py (the compiler: plan → bie.show-spec/1, or a refusal naming every wrong step); the review page | scenes over narration lines, each a list of steps in the plan vocabulary (bie/brain/video/engine/plan_vocab.json); times are cue words into the narration | 2026-11-03 |
| saancha_manifest | `bie.saancha-manifest/1` | `bie/brain/video/engine/saanche.json` | a reviewed PR beside its drawing in draw.mjs (Claude, or BIE's coder) | bie/brain/saanche.py (search, parameter checks); the scene-plan compiler (part B2); tools/saanche_stills.py (the CI still sheet) | every drawing the showing engine can make: anchor, parameters with types, defaults and limits, Hindi and English words, licence and provenance | 2026-11-03 |
| respec | `bie.respec/1` | `RESPEC.json` | tools/respec_video.py | the render workflow; Navin | a canvas run's plans compiled again with today's code: per video its parts compiled or refused with the reason | 2026-11-03 |
| text_audit | `bie.text-audit/1` | `audit.json` | tools/text_audit.py (bie/brain/video/text_audit.py) | the render report; the render workflow's gate; Navin | the texts of a rendered video measured on its frames: those whose settled size stays under the readable floor (CV-17) and those that cover each other, with when; since 5 November 2026 also (optional fields, same version) `overlap_seconds`, `longest_overlap_s`, `plan_marked`, a small text's `plan` flag and the `gate` (box rule: no overlap held over 2 s, no plan text under 36 px) | 2026-11-05 |

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
  part_whole, place, change, promise, question, other; `other` carries a note, logged in `relations_outside_list` so Navin can add an
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
- **Pictures the maker draws**: a canvas node may carry `picture` (a `timeline`, `gallery` or `flow` with its events, panels or
  steps); `plan_from` turns it into a `picture` node the same way as the book's, so the same compiler and checks apply.
- **Photos and objects** (`image_wanted` on a beat): a photo or museum object the beat names (a coin, a seal, a cheque) is looked
  up in the shared library; an image not found is a need of kind `image`. A portrait or likeness of a person is never wanted
  (card rule 8; historical figures are Navin's decision).
- **The fetch step** (`tools/task046d_fetch_needs.py`, GitHub Actions only, `.github/workflows/task046d-fetch-needs.yml`): reads a
  `needs.json`, looks in the shared library first, then in The Met Open Access (CC0), Openverse (CC0, CC BY, PDM) and Wikimedia
  Commons; every file passes the licence gate (`bie/toolbox/licence.py`: never BY-SA or NC), is tagged with the need's words and
  credited, and goes to `blindtest-results:library/`. Its report is `bie.brain.fetched/1` (per need: `fetched`, `in_library`,
  `not_found`, `skipped`, with the sources tried). A canvas run reads that library first (`tools/run_brain.py --library <https
  base>`, `assets.seed_library`: each file's licence and sha256 checked again on the way in). No source that needs a key.
- **Stills and LOOK-D1**: the render workflow publishes one 640 px still per part (`runs/<dest>/stills/<scene>.jpg`, listed under
  `stills` in `join.json`, an extra key the `bie.render.join/1` format allows, so its version stays). `tools/task046d_look_request.py` builds a `bie.look-request/1` with rule `LOOK-D1` (per part: the
  still and the teacher's point from the dikhane ki list); the VM's look section (`tools/vm_look.py`) asks the reviewer route,
  under the cost guard, whether the picture alone hints at the point (1–10) and whether it is text only. Report only: LOOK-D1
  never stops a video.

## 8. Kriya ke saanche, story goods, layout and meaning (Task 046 Part D2, Navin's verdict of 1 November 2026)

No format changes version in Part D2: every new key is optional, and the readers allow unknown keys (`formats.O`).

- **An action** (a canvas node of kind `action`, or a world element of kind `action`): `template` (one of
  `bie/brain/video/saanche.py` `TEMPLATES`: hand_over, pay_change, barter_swap, upi, card_tap, cheque, coin_count, refuse, accept,
  count_stack), `actors` [{role, who main/other, label, mood neutral/pleased/unsure/refusing}], `objects` [{name, icon, label}],
  `amounts` [{name, text}] (each number said in the action's beats, CV-16), `steps` [{name, cue}] in the template's order,
  optional `close_up` (false: no camera move) and `until_cue`; a world action has `x` on the street, a canvas action a `cell` of at
  least 3 rows. The maker's strict answer carries it as `action` {template, actors, objects, amounts, steps, close_up} on every
  node or element (`template` "" when unused). Compiled (`saanche.compile_action`): `step_at` {step: frame}, `actors` with `look`
  and `main`, `objects` {name: {src, icon, label}}, `amounts`, `at`, `until`, `items` (count_stack), `close_up` {at, until, step};
  a world action also `x` and `on_place`. The block is `bie/brain/video/blocks/toolbox/saanche.tsx` (`ActionStage`, a 1000 × 620
  stage, feet on y 600), drawn by `world_scene` and `canvas_build`.
- **Story goods in a world**: a shop's `goods` [{icon, label}] (required when it has `packets`), a crowd's `carry.icon` (required
  when it carries), a balance's `left` / `right` {icon, label}; compiled with `src` from the lesson's library. `world.icons_in`
  lists them for the library and the credits.
- **The visual-idea beat** adds `template` (a recipe, `compose`, `none`, or `other`) and `template_note`; the dikhane ki list keeps
  both per beat and, after the plan, `realised` (whether the beat's relation is shown). A process no template fits is a missing
  capability of kind `block` named `process: <note>` in `needs.json`.
- **The checks** (`canvas_director.check_plan`): `world.goods_problems`, `world.layout_problems` (overlaps, one board, label or
  title at a time, no number on a label or the title, the subtitle strip on the eased camera, the action's people at least a
  quarter of the frame tall, no empty camera key), `canvas.subtitle_problems` (both cameras, eased as the renderer eases them),
  `visual_thinking.meaning_problems` (relations realised on their beats, the struck-value rule); rules D2-01 … D2-05 in
  `visual_verbs.json` (2026-11-01.1), whose relations also name their saanche. `visual_thinking.icon_misfits` is a report.
- **Report keys**: `canvas.json` rows' `report` and `quality` add `actions`, `relations`, `relations_realised`,
  `relations_realised_pct`, `boards_in_world_parts`, `overlaps`, `subtitle_violations`, `icon_misfits`.
- **Stills and LOOK-D2**: the render workflow also publishes one still per beat at 65 % of the beat
  (`runs/<dest>/stills/<scene>/<beat>.jpg`, from the captions' `beat_id`). `tools/task046d_look_request.py --rule look-d2` builds a
  `bie.look-request/1` with rule `LOOK-D2`: per part up to 8 beats, each with its still, what it should show and its items (the
  dikhane ki list's nouns, its relation, its process). The VM's look section asks only visible yes/no and happening yes/no per item
  (`look.D2_SCHEMA`); `look.d2_score` computes the part's score (10 × (visible + happening) / (2 × items)). Report only.
- **Pictures**: the icon index (`bie.icons/1`, unchanged) adds the `fl:` set (Microsoft Fluent Emoji 3D, MIT, pinned commit). The
  `bie:` set of BIE's own money drawings was retired on 2 November 2026 (§8c).

### 8a. Saanche from general motion parts (Navin's addendum of 2 November 2026)

Navin: "jis cheej ka jikar hai wohi cheej dikhe" — examples are illustrations, not a list. No format changes version: the new keys
are optional and the readers allow unknown keys.

- **The parts and recipes** are data: `bie/brain/rulebook/saanche.json` (`bie.brain.saanche/1`): the motion parts (hold, give,
  move, transform, show_text, meter, appear, refuse, accept, compare), the named spots of the stage, the recipes (each a
  composition of parts per step, with roles, objects, optional objects and amounts), the relations each part realises, the words
  that hint a recipe. `saanche.TEMPLATES` is read from it; `template` may also be `compose`.
- **An action** adds `texts` [{step, text}] (a short word the narration says, shown with that step's sign) and, for
  `template: compose`, `parts` [{part, cue, actor, from, to, object, into, on, text, style, inside, n, spot, back, left, right,
  sign, left_text, right_text, limit, dir, title, reach}] (only the fields a part needs; actors and objects are the action's own).
  A recipe's object the plan leaves out is optional: a plain chip with the part's text, or its parts are skipped. An object the
  recipe has no place for is dropped (a fix in `auto_fixes`). The maker's strict `action` carries `texts` and `parts` (empty when
  unused).
- **Compiled** actions add `parts` [{part, at, … the resolved fields}] in time order (actors as slot numbers 0 and 1, objects by
  name, targets as {actor} / {object} / {spot}, texts filled from the amounts and labels, `until` on a sign, `end` and `items`
  on a meter or an appearance); `objects` may hold `{chip: text}` instead of `{src}`. The block draws only these parts and only the
  plan's own pictures: no object of its own (`tests/test_task046d2_general.py`).
- **Places** are data: `bie/brain/rulebook/places.json` (`bie.brain.places/1`), the words that name each place; a place's sign
  is only the plan's own `sign` (no default name).
- **What code reads in a composed process** (`saanche.settle_compose`, 2 November 2026): a style the part has no use for is
  dropped (a show_text style outside STYLES is a tag; a meter's own styles are `meter_styles`, bar and number); a place word is
  its spot (`spot_words`); a count is brought into 1 .. 12; the only actor or object fills a part that left it out; a move named
  by `from` or `spot`, a meter whose value is its `text` (or the last amount said), a compare of the action's two objects (or of
  one object with two texts) are read that way; an object without its icon takes the icon that is a picture of it.
- **One camera at a time** (`canvas.one_camera_at_a_time`): the block camera stays on the whole canvas, and an action's close-up
  waits, while the plan's scene camera is zoomed in.
- **Lexicons** of the meaning checks (return words, change words, old-days words, modern icons) are data in `visual_verbs.json`
  (`lexicon`). A value given back is refused as a struck value only when a return word stands beside that value (or a change word
  is in the beat), and a process with a `give` on the beat shows it instead.


### 8b. Every mentioned thing on screen (Navin's addendum of 2 November 2026, point 4)

"jis cheej ka jikar hai wohi cheej dikhe": every thing the dikhane ki list names for a beat (`things`) must be on screen during
that beat. No format changes version: the new keys are optional and the readers allow unknown keys.

- **Shown** (`visual_thinking.coverage_rows`): an element is on screen from its first cue (frame 0 when it has none) to its
  `until_cue` (or the part's end); in a world, the kit's place and the person who works there stand for the whole part
  (`places.json` `whole_part`). A thing is shown in a beat when an element on screen then draws a picture of it (the icon
  candidates code offered for it, the library's pictures of it, an icon whose name or terms carry its words), or, in a world, is
  of a kind that draws it (`places.json` `draws`: a shop draws the shop, the crowd its people), or is an action whose actor is
  it; a mark of the visual grammar (tick, cross, arrow, question mark, equal sign; `visual_verbs.json` `lexicon.mark_things`) by
  a mark, an arrow or a motion part; a number, label or tag (`lexicon.text_things`) by the words of an element on screen.
- **A picture OF the thing** (`toolbox.icons.fits`): an alias names the icon for it, or every content word of it starts a word of
  the icon's name or terms ("payment claim" is not a baggage claim). Only a thing BIE has such a picture of is asked for; one
  without is reported (and is a need for the general asset path), never refused.
- **Code shows what it can** (`visual_thinking.show_missing_things`, canvas only): up to `AUTO_THINGS_MAX` (4) things per part
  that BIE has a picture of but the plan leaves out get an `icon` node `auto_thing_<n>` in a free area of the grid (2 × 2, else
  2 × 1, else one cell) during the beat, cued on the thing's word when the beat says it, leaving when the next beat starts.
  A world is left to the maker.
- **The check** (`canvas_director.check_plan`, both modes): a thing with a picture not on screen in its beat is refused, with the
  thing and its pictures named. A thing named by a text or mark head noun (`visual_verbs.json` `lexicon.text_heads`) is shown by
  the words on screen (its numbers, its currency or per-cent sign, its words) and is never asked for as a picture.
- **The library's pictures of a thing** (`AssetLibrary.pictures_of`, read by the needs list and by BIE's coder alike): a fetched
  picture by a tag that is the whole thing (the coder: or every word of it); a drawing by BIE's coder only by its own thing (the
  spec in its `prompt`), its title or a phrase tag, or by their head noun with every word of the thing among its words, never by
  a single tag its maker chose. One coder run draws a thing once: another phrasing with the same head noun and no new word
  ("merchants", "silver piece" after "shaped silver piece") is left to the drawing made for it (`coder.drawn_as`).
- **Report keys**: each passed part row of `canvas.json` adds `coverage_pct`; each part of the dikhane ki list
  (`visual_ideas/<video>.json`) adds `coverage` {mentioned, shown, coverage_pct, not_shown [{beat_id, thing, has_picture}]}; each
  video's `report` adds `mentioned_things`, `shown_things`, `coverage_pct` and `things_not_shown` [{beat_id, thing, has_picture,
  part}]; `quality` adds `mentioned_things`, `shown_things`, `coverage_pct` and `things_without_a_picture`; `CANVAS.md` shows them.

### 8c. One general path for every thing a beat names (Navin's addendum of 2 November 2026, point 1)

"Nothing is hand-made for one chapter. Whatever a beat names goes through the one general path: library -> icon index (incl.
Fluent Emoji) -> fetch -> if still missing, BIE's own coder makes a new SVG component from a short spec, tested and
licence-clean, and adds it to the library for every later book."

- **Retired**: the `bie:` set (26 money drawings, `tools/bie_objects.py`, `bie/toolbox/icons/bie/`), its index rows and every alias
  that named it; the registry keeps `bie-objects` as `blocked_with_reason`. An id of the set still parses, so `check_ids` names it
  as not in the index (an earlier plan that uses one is refused, and its maker continues from it).
- **The words of the search** are data: `bie/toolbox/icons/aliases.json` (`bie.icon-aliases/1`), vocabulary (Hindi words,
  synonyms, emoji names) that points at existing icons, never a list of things to draw.
- **A picture OF the thing** (`toolbox.icons.fits`, also used by `resolve_needs`): an alias naming the phrase's head noun ("debt
  ledger" → the ledger; "sack of salt" is a sack, not the salt shaker), and then the alias decides; otherwise every content word is
  a whole word of the icon's name or terms. Only fitting icons are offered to the maker; a thing with none is a need.
- **BIE's coder** (`bie/brain/coder.py`; `tools/run_brain.py --section coder --from-run <canvas run> [--library <shared library>]`;
  VM job section `coder`): for every need of kind `icon` or `image` the coder may draw (`coder.wants`: never a person, a name, a map,
  a flag, a logo or a copy of real money) and the library lacks, code writes a short spec and the maker writes one SVG
  (`rulebook/coder_card.md`). `coder.svg_problems` checks it (one `<svg>` root in the SVG namespace, a square viewBox, only the
  allowed elements and attributes, no script, link, image, style, font, entity or words, `url()` only to an id of the same file, at
  most 400 elements and 40 KB, at least 3 shapes, something visible) and sends the problems back; a passed file is stored cleaned
  as `made/<slug>.svg` with `made.json` (`bie.brain.coder-made/1`) and `MADE.md`.
- **Into the library**: `tools/task046d_fetch_needs.py --made <made.json>` (the fetch workflow's `made_url`) reads every drawing,
  checks its sha256 and `svg_problems` again and adds it to `blindtest-results:library/` as source `bie_coder`, licence CC0 1.0,
  with `generated_by`, `prompt` and `generated_on` (the licence policy's `generated_images`, Navin's decision of 29 October 2026;
  `bie/brain/assets.py` `Asset` carries the three fields). A canvas run then finds it first (`resolve_needs` images).
