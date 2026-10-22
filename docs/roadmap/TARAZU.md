# TARAZU · the 5-point audit of every BIE section

Task 043 · 22 October 2026 · main after PR #41 (`c8853eb2`) · Owner: Navin · Written by Claude

The tarazu (scale) is the test every section must pass before BIE is judged as one whole system. It weighs
each old section (Sections 1–18 of the original BIE) and each new brain module (`bie/brain/`, Tasks 039–042)
against Navin's five points, and decides what happens to it: **use** as it is, **extend** it, or **replace** it
and retire the old one explicitly. There is one BIE: no parallel systems survive Phase 1.

## The five points

| # | Point | What passing means (Navin, 22 Oct 2026) |
| --- | --- | --- |
| 1 | Understanding | Two eyes (text + page image); question-based teacher understanding (kya, kyun, kaise, kab, kaun, kahan, tulna, saboot, nateeja); every teachable thing covered |
| 2 | Teaching and video | Universal frame (process, how, when, conditions, atmosphere); subject style; visual mathematics; spoken Hinglish like Navin; programmatic video code (no AI video models); anatomy-level visuals |
| 3 | Game | Learning itself is the game; chapter-wise; nothing missed; no drift; no hidden quiz; chapter games join into one book world |
| 4 | Notes | Navin's summariser design: question-based; three depths; "kitaab mein nahi bataya gaya"; source pages; "book says" separate from "latest update" (with link and date); code-drawn infographics; slides + PDF |
| 5 | Review and lock | Code checks, an independent reviewer AI, Navin's verdict; full process record per section; passed rules, formats and examples get locked |

## Where BIE stands on each point today

Status words as in `CLAUDE.md`: IMPLEMENTED (code exists), INTEGRATED (real upstream in, real downstream out on
a real book), ACCEPTED (Navin passed it). Nothing below is ACCEPTED.

| Point | Today | Biggest missing piece | Fixed by |
| --- | --- | --- | --- |
| 1 Understanding | Section 1 INTEGRATED on the tissue chapter (10 of 14 pages and the map passed in live runs; 525 items, 1,091 teacher questions). Task 045 PR A (offline): BIE's nine content types with code proposals, required questions per type, task cards and the naksha IMPLEMENTED | The cards, types and naksha have not run live; untested on other subjects | 045 PR B |
| 2 Teaching and video | Lesson, director and visual sections IMPLEMENTED, run offline only; preview renderer makes silent stills and MP4s | No voice; no real render; no interactive player; two scene formats; subject styles only in prompts | 046, 047, 048 |
| 3 Game | Game design IMPLEMENTED (offline); a self-contained phone runtime and a bot exist; the builder is a draft | Builder not wired; two game runtimes (brain and Section 15); no book world | 049 |
| 4 Notes | Notes section IMPLEMENTED (offline): question slides, three depths, source pages, "book does not say", code-drawn infographics, HTML deck with print view | No "latest update" with link and date; no slides/PDF export step; not run live | 050 |
| 5 Review and lock | Code checks and an independent reviewer per step; full process record per step; rulebook versioned | No Navin verdict flow, no locking of passed examples, no test set, no review page; Section 16 QA, 17 EVAL and 18 APP not connected to the brain | 051, 052 |

## The five biggest gaps

1. **Review and lock is not built (point 5).** Process records are written, but nothing records Navin's
   verdict, turns a failed verdict into an approved rule, locks a passed output as an example, or reruns a
   locked test set when code, a rule or a model changes. Sections 16 (QA), 17 (EVAL) and 18 (APP) already
   do much of this for the old pipeline and are not connected to the brain. → **051** (review page on the
   Section 18 operator app, verdicts, locks) and **052** (locked test set rerun).
2. **No voice (point 2).** The brain has no narration; word timings are guessed from the text (130 words a
   minute). Section 14 has eSpeak (robotic) and an ElevenLabs adapter, but nothing is wired and the AUDIO
   reconciliation is open. → **047** (extend Section 14: tested natural and cloned voices, word timestamps
   drive the animation).
3. **No real render and no player (point 2).** The brain renders silent previews with `remotion-lite` (a
   small copy of the Remotion API) in Chromium; the real compiler (Section 13, COMP) is not wired after
   Scene IR, and there is no interactive player. → **046** (silent video from the director), **048** (real
   Remotion render through COMP, frame QA, interactive player).
4. **The game is half built (point 3).** The designer works offline, the builder is a draft that
   `run_brain` does not call, the brain runtime has three engines (drag, branch, slider) while Section 15
   has 17 mechanic types with state, mastery and adaptation, and chapter games do not join a book world.
   → **049** (one engine decision, builder, bot playtest, book world).
5. **Understanding is not yet shaped for scale (point 1).** Content types are free text, every later section
   re-sends a large chapter map (cost and drift), instructions are long prose rather than compact task cards,
   and only one chapter of one subject has run. → **045** (compact chapter map, content-type detection,
   task cards, merge with KI/PR/RE/PED; tissue + 4–5 other chapters).

Also open, smaller: notes lack "latest update with link and date" (**050**); the asset finder reaches only
Wikimedia Commons and cannot read part locations from SVG text (**046**); a same-company checker is in use
while only the Gemini key works (**044** brings ChatGPT Pro as maker).

## Old sections (the original 18)

Sizes are Python files and lines under `bie/` today. "Live" means used by the 11-stage productized pipeline
(SOURCE → … → SCENE_IR) or by the brain.

| Section | What exists | Points | Gap | Decision | Task |
| --- | --- | --- | --- | --- | --- |
| **INFRA** (`bie/infrastructure/`, `bie/bie_core/`; 76 files, 3.4k lines) | Durable task queue, content-addressed artifact store, idempotency, leases, lineage, event stream, execution graph, sandbox, render worker image, Postgres/object-store adapters; the pipeline's persistence and recovery | 5 (records), all (runs) | Brain writes its records and outputs as loose JSON files; no lineage from a lesson back to its process records; resume only through `--resume-from` | **Use + extend**: brain records, locked examples and chapter maps go into the artifact store with lineage | 051 |
| **MODEL** (`bie/model_gateway/`; 47 files, 2.3k lines + `live/`) | Thin adapters, schema validation, retry, provenance; `live/`: real Anthropic, OpenAI, Gemini and AICredits clients, LiveGateway, ledger, disk cache; Task 043 cost guard | all | Routes keyed by provider (same-company checker is a temporary exception); Codex route built in 044 (`codex_client.py`, subscription billing, plan-limit stop), live once the private machine exists; no batch mode or prompt caching in use; older routers (`capability_router`, `fallback_router`, `semantic_cache`, `context_budget`, `quality_escalation`) unused | **Extend** `live/` as the one gateway; wire or retire the unused routers when cost work starts | 044, 052 |
| **BI** document intelligence (`bie/document_intelligence/`; 93 files, 3.0k lines) | Real PDF text runtime (native text blocks with ids such as `p0003-b0007`, headings, TOC); OCR, figure, equation and layout modules mostly as contracts | 1 | Image-only pages (tissue pages 2, 7, 8) have no text; OCR not wired; text/image disagreements are flagged by the AI, not resolved by code | **Use** the text runtime as eye 1; the brain's page image read by a vision model is eye 2 (already built); OCR modules stay as a check for scanned and Hindi pages | 045 |
| **KI** knowledge (`bie/knowledge_intelligence/`; 82 files, 0.5k lines) | Mostly small contracts (claims, concepts, definitions, evidence); the live KNOWLEDGE stage is lexical extraction (`productization/candidates.py`) | 1 | Lexical candidates are not understanding | **Done in 045: replaced and retired.** Brain Section 1 is BIE's understanding; `candidates.py` is retired (no brain code may import it, a test enforces it). Used as checks on the chapter map: `ki_coverage_qa` (high-exam items are critical), `knowledge_graph_orphans`, `definition_consistency`. The 11-stage technical pipeline keeps the file as a regression fixture until 051 replaces its KNOWLEDGE stage | 045, 051 |
| **PR** prerequisites (`bie/prerequisite_intelligence/`; 30 files, 0.6k lines) | Graph, transitive reduction, cycle resolution, teaching order, bridge contracts; live producer accepts only explicit lexical statements (`productization/pr_reasoning.py`) | 1, 2 | No cross-chapter prerequisite graph yet | **Done in 045: producer replaced and retired; graph used.** The map's `depends_on` links are checked: no circle (`find_cycle`), every prerequisite taught before what needs it (`teaching_order` proposes a valid order), redundant links recorded (`transitive_reduction`). Book-level graph later | 045, 051 |
| **MATH** (`bie/math_intelligence/`, `bie/notation_intelligence/`; 61 files, 0.8k lines) | Equation AST, unit parsing and conversion, dimensional analysis, numeric equivalence, derivation checks (bounded) | 2 (visual mathematics), 5 | Brain visual mathematics (scales, charts) is AI-only; numbers are not checked by code | **Extend**: unit and number checks verify "facts and numbers" items and the director's to-scale visuals | 045, 046 |
| **RE** reasoning (`bie/reasoning/`; 120 files, 3.5k lines) | Decision contracts, causal graphs, chronology and event order, evidence arbitration, abstention; live use limited to graph order (temporal and causal interpretation deliberately not executed) | 1, 5 | Only concept-level links are checked; item-level event order not yet | **Done in 045: extended.** `graph_cycles` refuses cause-effect circles; `chronology_reasoning` (`year`, `relation`) refuses `sequence_next` and `causes` links between dated concepts that go back in time | 045 |
| **PED** pedagogy (`bie/pedagogy/`; 59 files, 1.4k lines) | Objectives, sequencing, misconception confrontation, cognitive load, duration estimation, mastery, assessment blueprint; live stage composes records and writes no narration | 2 | Mastery, misconception and assessment modules not used yet | **Done in 045: planner replaced and retired; QA used.** `pedagogy_plan.py` and `pedagogy_slice.py` are retired like KI. Section 2 checks: `objective_coverage_qa` (every card item taught), `cognitive_load_qa` (a heavy beat is split), `prerequisite_coverage_qa` (every prerequisite bridged), `lesson_duration_estimation` recorded beside the script's spoken length (a script under half its planned minutes is sent back) | 045 |
| **DIR** director (`bie/director/`; 71 files, 9.6k lines) | Script plan, narrative arc, hooks, dialogue, pacing, emphasis, narration sync, factual-script QA, game handoff; parked Step 4–6 branches; live stage is template-driven | 2 | Two directors; the brain director has no story mode and no pacing or repetition checks | **Replace** the template director with brain Section 3; **extend** with old `pacing_qa`, `repetition_detection`, `script_coherence_qa` as code checks; story mode from `narrative_arc`/`hook_strategy` where the content type fits; recommend dropping parked Step 4–6 (Navin decides) | 046 |
| **VIS** visual (`bie/visual_intelligence/`; 84 files, 4.2k lines) | Subject grammars (biology cellular, chemistry, data chart, geography map, history timeline, process flow, physics vector, maths graph), layout solver, collision avoidance, label placement, readable size, contrast, asset contracts and need detection | 2, 4 | Brain visual checks overlap and text size with its own code; the old layout QA and grammars are unused; two asset models | **Extend**: brain layouts pass through old collision, label-placement, readable-size and contrast checks; grammars become the per-content-type visual patterns in `content_types.json`; one asset library (brain `assets.py`, licence fields aligned to VIS asset contracts) | 046 |
| **ANI** animation (`bie/animation_intelligence/`; 67 files, 2.6k lines) | Attention model, easing semantics, camera movement, reveal and morph selection, process animation, global timeline solver, excessive-motion and synchronisation QA | 2 | Brain block library animates itself; no motion QA on brain VideoSpecs | **Extend**: excessive-motion, competing-motion and synchronisation checks run on brain VideoSpecs; the brain block library is the one animation layer | 046, 048 |
| **DSL** Scene IR (`bie/scene_ir/`; 80 files, 2.8k lines) | Typed scene document (chart, diagram, equation, map, 2D/3D model, particles), animation tracks, narration cues, interaction bindings, schema and semver, compiler preflight; live: one scene (Task 036) | 2 | Two scene formats: Scene IR and the brain VideoSpec (layers, camera keyframes, word cues) | **Decide at the start of 046** (Navin's video path A/B). Recommended: VideoSpec becomes a Scene IR profile through one adapter, keeping Scene IR's schema, versioning and interaction bindings; **retire** the Task 036 single-scene producer path | 046 |
| **COMP** compiler (`bie/compiler/`; 132 files, 13.2k lines) | Scene IR → Remotion project (deterministic codegen, component registry, chart/equation/diagram compilers, captions, audio cue sync, asset bundler), full render, generated-code lint and static analysis; CI renders 48-frame fixtures | 2 | Not wired after Scene IR; the brain uses `remotion-lite` (preview only, no audio) | **Extend**: COMP compiles the brain block library (already written against the Remotion API) and renders real video with its build, font-coverage and content-fit checks; **retire** `remotion-lite` from final output (it stays for fast review stills) | 048 |
| **AUDIO** (`bie/audio/`; 105 files, 11.7k lines) | ElevenLabs adapter (opt-in), eSpeak (offline, robotic), TTS cache, voice selection, pronunciation lexicon (acronyms, maths), caption alignment, loudness, ducking, mix pipeline, animation sync; `AUDIO_REPLAN_REQUIRED` open | 2 | Not in the pipeline; no natural or cloned Hinglish voice tested; no word timestamps reach the brain | **Extend** Section 14: tested voice providers including a cloned voice, word timestamps feed `bie/brain/video/timing.py`; no new audio system | 047 |
| **GAME** (`bie/game_engine/`; 201 files, 6.0k lines) | Section 15 engine: 17 mechanic types (sequencing, simulation experiment, construct model, branching scenario, map interaction, timeline reconstruction, prediction-observe, diagnose error, classify-sort and more), state, mastery, adaptation, pinned React runtime, QA engine; sealed runtime bindings | 3 | Not wired; the brain has its own runtime with three engines; no book world | **Decide in 049**. Recommended: **extend** Section 15 (its mechanics already match the content types; it has mastery and adaptation) with the brain game designer as its director and the brain bot as its playtester; port the brain's picture boards; **retire** `bie/brain/game_runtime.py` engines after the port | 049 |
| **QA** (`bie/qa/`, `bie/section16/`; 283 files, 23.9k lines) | Section 16 v2 suites: source, semantic, pedagogy, director, visual, animation, audio, video (media checks), game, maths, reasoning, rights (licences), security, regression, reproducibility, repair, release | 5 | Runs on fixtures, not on brain outputs; brain checks are per section; no frame-level QA of brain videos; rights QA not applied to brain assets | **Extend**: brain code checks call Section 16 suites where they fit (video media and frames, rights and credits, reproducibility, regression); no parallel QA. Inventory checks forbid new files in `bie/qa/` until converted | 048, 049, 052 |
| **EVAL** (`bie/evaluation/`; 138 files, 9.6k lines) | Benchmarks: metrics, domains, AV, browser, anti-gaming, native campaign, release admission | 5 | No benchmark over brain outputs; the locked test set does not exist | **Extend**: locked chapters and Navin's verdicts become EVAL benchmarks; a quality drop rejects a change | 051, 052 |
| **APP** (`apps/operator`, `apps/web/operator`, `apps/api`, `apps/android`) | Section 18 operator app: local service, per-stage producers with worker processes, artifacts, previews, quality and governance views, web UI; PDF inspection API with durable jobs; Android foundation | 5, one-button | Runs the old producers, not the brain; no page to watch, play, read and give a verdict in Navin's words; F-08 browser flake | **Extend** the Section 18 operator app into the one-button software and the review page; no new app | 051 |
| Productization glue (`bie/productization/`; 26 files, 6.2k lines) | The 11-stage durable pipeline that composes the old producers | all (orchestration) | Its thinking stages (KNOWLEDGE → SCENE_IR) are lexical/template | **Replace** the thinking stages with brain sections inside the same durable run; keep its persistence, fencing and recovery | 051 |

## New brain modules (`bie/brain/`, Tasks 039–042)

| Module | What exists | Points | Gap | Decision | Task |
| --- | --- | --- | --- | --- | --- |
| `rulebook.py`, `rulebook/vision-2026-10-21.json` | 38 versioned rules (G, S1–S7, R), each an instruction for the maker and a check for the reviewer; digest in every record | all, 5 | No rule born from a Navin verdict yet | **Use + extend**: `content_types.json` 2026-10-22.2 with code detection (045); S1-08 names the nine types and S2-06 adds the frame and teaching pattern (045); verdict rules (051) | 045, 051 |
| `runner.py` | Section runner: maker notes + output → code checks → reviewer (blocking/minor) → patch remakes, max 3 rounds → process record; Task 043 adds stopped status, models and reviewer independence; Task 045 adds the card, the prefix hashes and what code observed per round | 5 | Records only as files; nothing locks | **Use + extend**: task cards done (045); records into INFRA, locks | 051 |
| `cost.py` + `model_gateway/live/budget.py` (Task 043) | Cost guard: estimate, preflight, hard cap, rupees per section and page | all | Estimates for Sections 2–7 are assumptions until measured | **Use**; replace assumptions with measured numbers after each live run | 045–052 |
| `pages.py`, `understanding.py`, `content_types.py`, `naksha.py`, `cards.py`, `engines.py` | Section 1: two eyes, items with locations, question-based teacher understanding, chapter map, resume; since 045 on task cards with code type proposals, required questions per type, engine checks and the naksha | 1 | Not run live on cards; one subject tested | **Use + extend** | 045 PR B |
| `lesson.py` | Section 2: video plan, spoken Hinglish scripts in beats, coverage claims checked; since 045 on task cards with the universal frame, teaching-pattern steps and PED checks | 2 | Never passed live | **Use + extend** | 045 PR B |
| `director.py` | Section 3: scenes with the universal frame, subject style, anatomy-level elements, word-cued camera and actions, visual maths, pause questions, tap-to-explore | 2 | Offline only; visual maths not checked by code; no story mode | **Use + extend** | 046 |
| `assets.py`, `visual.py` | Section 4: asset plan, Wikimedia Commons search with allowed licences, choice by a vision AI, licensed library with credits, word-cued layouts reviewed on rendered frames | 2, 4 | Wikimedia only; no Openverse; no SVG part locations; no AI-drawn SVG fallback; not run live | **Extend** into asset finder v2 | 046 |
| `video/blocks`, `video/preview`, `video/render.py`, `video/timing.py` | Block library in the Remotion API, `remotion-lite` preview renderer (Chromium + ffmpeg), timing estimated from text | 2 | Not real Remotion; silent; timing guessed | Blocks **use** (become COMP components); preview **use** for review stills only; final render via COMP; timing from Section 14 | 047, 048 |
| `game.py` | Section 6 design: one game per chapter from the map; mechanic from content type; quiz-like missions rejected by code | 3 | Offline only; no book world | **Use** as the game director | 049 |
| `game_runtime.py`, `game_bot.mjs`, `game_build.py` | Self-contained phone runtime (drag, branch, slider), bot playtest with screenshots, builder draft | 3 | Builder not wired; duplicates Section 15 runtime | **Decide in 049** (recommended: port to Section 15, keep the bot) | 049 |
| `notes.py`, `notes_render.py` | Section 7: question slides, three depths, source pages, basis (book/outside/mixed), "book does not say", PYQ links, code-drawn infographics; one interactive HTML deck with print view | 4 | No "latest update" with link and date; no slide/PDF export step; offline only | **Use + extend** | 050 |
| `fake.py` | Deterministic offline maker and reviewer | tests | Proves execution, not quality | **Use** (tests only) | — |

## Known items checked

| Item | Finding | Task |
| --- | --- | --- |
| Notes lack "latest update with link and date" | Confirmed: `notes.py` marks basis and "not in book" but has no update field, link or checked date | 050 |
| Game builder half done; chapter games do not join a book world | Confirmed: `game_build.py` says "not wired into run_brain yet"; no book-world code anywhere | 049 |
| No voice | Confirmed: no TTS call in the brain; Section 14 not in the pipeline | 047 |
| Render and player not wired | Confirmed: silent preview MP4s only; no interactive player | 046, 048 |
| Brain video_specs vs Scene IR | Two formats for the same thing; recommended adapter (VideoSpec as a Scene IR profile) | 046 |
| Brain game_runtime vs Section 15 game engine | Two runtimes; recommended port to Section 15 | 049 |
| Brain preview renderer vs COMP compiler/Remotion | Two render paths; COMP for final output, preview for review stills | 048 |
| Brain checks vs Section 16 QA | Brain checks are per section; Section 16 suites unused on brain output | 048, 049, 052 |
| Review page vs Section 18 operator app | No review page; build it into the operator app | 051 |
| Section 14 audio | Large engine, not wired, reconciliation open | 047 |

## How this file is used

- Each task from 044 to 052 starts by reading its rows here and ends by updating them (state, gap, decision
  taken). A "replace" is finished only when the old path is retired explicitly (removed from the live
  pipeline and noted here), never by leaving both running.
- Retired in Task 045 (no brain code may import them; files kept as regression fixtures of the 11-stage technical
  pipeline until 051): `bie/productization/candidates.py` (KI), `bie/productization/pr_reasoning.py` (PR),
  `bie/productization/pedagogy_plan.py` and `bie/productization/pedagogy_slice.py` (PED). The list lives in
  `bie/brain/engines.py` (`RETIRED_MODULES`).
- Navin's decisions recorded here: none yet. Open: video path (A Scene IR compiler or B brain path, at 046),
  game engine (at 049), parked Director Step 4–6 (drop recommended).
