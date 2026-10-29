# BIE Status

Updated: 27 October 2026 · Read this first in every new session, then show Navin the current task card.

## Now

| Field | Value |
| --- | --- |
| Phase | 1 · BIE as one whole system; plan agreed on 22 October 2026 (ROADMAP, "Agreed on 22 October 2026") |
| Current task | **Task 046 · Part C (Economy): "B default ke saath kahani wale hisson mein C"** (Navin, 27 October 2026). The economy kit of the asset intake joins BIE and makes ONE real video from Navin's sample economy chapter, one PR per piece. **PR 1 (`task046c-kit`, PR #82): the kit inside BIE** — the `canvas_build`, `curve_story` and `world_scene` blocks in the toolbox bundle, the plan compilers `bie/brain/canvas.py` (B: L2 + touches) and `bie/brain/video/world.py` (C: L3), the danda bug fixed in `timing.py`, one caption place (the core strip), Twemoji and Font Awesome Free as CC BY 4.0 icon sources with the credit roll, the canvas rules CV-01…CV-12 in the rulebook, five proof clips, 28 tests. **PR 2 (this branch, on top of PR 1): the director's canvas (B) and world (C) modes** — `bie/brain/canvas_director.py`, `--section canvas` in `tools/run_brain.py` and the VM runner, the AI plan step on the director card through the SectionRunner, a refused plan back with the exact code error, first-try passes and rounds counted per part, 13 tests; **plus Navin's addition of 27 October 2026 (\"economic concepts ko real world mein apply karke samjhao\")**: the `real_world_application` method, the `real_world_example` slot for economics definition / cause-effect / process items, rules S1-16 (the slot filled, checked by code) and S2-08 (the example runs with its numbers before the term is named), the example's beats as the director's story piece, 15 tests; the proof on the Money chapter runs on the VM after the merge. **PR 4 (`task046c-render`, PR #86, merged, on top of PR 2): render speed** — frames captured straight from Chromium's compositor and the page composited in software (0.62 → 0.26 s a frame on a plain canvas, 0.86 → 0.30 with touches, 1.61 → 0.37 for the world, same pixels), no per-frame blur or drop-shadow filters, static world layers cached, `tools/render_spec.py` (chunk / join / measure / bench / fixture) and the `BIE Task046c Render` workflow (parallel chunks on several runners joined into one MP4, the full MP4 as a CI artifact, the ≤ 720p review copy on `blindtest-results`), 8 tests. Next: PR 3 world kits for the chosen video's places; then the real video and STOP for Navin's verdict. The one-shot test (PR #76, draft) and Part B (PR #75) stay unmerged; their records are in the sections below. Cost so far ₹0 (no AI call) |
| Branch | `task046c-lesson-notes` (the lesson seekh, PR #94; from `main` after PR #93); then `task046c-video` |
| State | **29 October 2026, work B (branch `task046c-coverage`, on top of work A; IMPLEMENTED by tests and on v1's real outputs; ₹0):** every review page can say by code which book lines the video taught (`bie/brain/coverage.py`, table B on `tools/task046c_page.py --lesson --chapter-map`, the chapter page `tools/task046c_chapter_page.py`): v1 13 of 13 lines in 32 timed beats, 0 not covered; the chapter 383 of 383 lines assigned, 246 taught by a passed video, 137 waiting in the five failed scripts. **29 October 2026, Navin's verdict on Money v1 ("achha laga ki us concept ko real world example se samjhaya gaya ... teacher ki naration uske sentence aise poore ho ki banawati na lage"; the direction confirmed, nothing ACCEPTED yet) and work A of the work after it (branch `task046c-screen-text`; IMPLEMENTED by tests; INTEGRATED when v1's re-run passes under the new rules; ₹0):** on-screen text is a complete phrase the narration explains (CV-13 to CV-16 in `canvas_profile.json` 2026-10-29.1, checked by `bie/brain/video/screen_text.py` in the director's plan check), the narration speaks like a teacher (S2-09 in the vision rulebook 2026-10-21.15, `soul.state_report_problems` in the script check; Navin's line in `teacher_examples.json` 2026-10-29.1), a board holds a complete sentence (3 lines of 40), the lock tool locks the narration wording of locked examples, the review page shows the before/after by code. **Before, on v1's own outputs:** 93 of 186 on-screen texts fail the new checks (CV-14 38, CV-13 37, CV-16 17, CV-15 1); 29 of 886 Money beats (v1: 4 of 32) are state reports. Next: v1 again through BIE (script resume, plans, render), the before/after on its page, the narration lock; then works B to E (section "Navin's verdict on Money v1 and the work after it"). Earlier the same day, **29 October 2026, Navin's decisions recorded and built (branch `task046c-navin-decisions`; IMPLEMENTED by tests; the library-first read INTEGRATED only when the next real understand run counts its hits; ₹0):** v1's real-world examples locked (11 of its 13 items carry one; `explanations.json` 2026-10-24.2; narration wording not locked, waits for the narration work), BIE reads the library first and the run report counts library hits against AI examples (replay on the Money map: page 1 11 of 11 items from the library, the whole chapter 18 of 96 with 0 of the 85 other items touched wrongly), `docs/bie/CONTRACTS.md`; PRs #75 and #76 closed; Route 2 chosen for science hero shots and generated images allowed with their provenance; India Code, the SRTM15+ relief and BodyParts3D approved by name, Hipparcos waits for ESA's terms with the Yale Bright Star Catalogue as the default star source, India's boundary keeps its condition, Remotion decided (section "Navin's decisions of 29 October 2026" below). **Works A and B of the same brief were not received by BIE; the examples' narration lock waits for work A.** Earlier, **28 October 2026, the real video is rendered: v1 of the Money chapter ("Money क्या है, और हमारे कौन-से काम करता है?"), 7 minutes, silent with captions, every plan by BIE (INTEGRATED: the lesson section's script → the director's canvas and world plans → the kit → the CI render; nothing ACCEPTED before Navin's verdict; AI ₹0 on the ChatGPT plan, render billed ₹0):** section "The real video" under "Task 046 · Part C (Economy)" below. Plans `t046c-money-canvas-v1c` (8 of 8 parts, 6 first try, 11 rounds, B 2 / C 6, 3 of 3 story parts in a world, 416.5 s, 13 Codex calls in 9.8 minutes); render run 40630915969 (6.94 minutes of video, 8 chunks, 3.6 minutes wall-clock, 25.5 machine minutes, 0.122 s a frame, ₹17.1 at the list price); review copy `blindtest-results:runs/t046c-money-v1c/review-720p.mp4` (14.9 MB), the full 1080p MP4 in the run's artifacts; the review page (private): https://claude.ai/artifact/UVqeuVEtVKW3dmMfUKJqKS. The first render (`t046c-money-v1`, run 40619059768) is the before of two seekhs: boards that held sentences (entry 23, PR #95) and a camera box that showed the backdrop (entry 24, PR #96); the page tool `tools/task046c_page.py` (PR #97). The lesson resume `t046c-money-lesson-d` measured seekh 22 live: 13 of 18 scripts pass (7 before), v5 and v17 pass at round 1 (bullet "The lesson resume"). **STOP: waiting for Navin's verdict on v1.** Earlier the same day, **28 October 2026, PR 3, the bank kit, merged (PR #93, `f99b77a6`; IMPLEMENTED by tests and five stills of the kit fixture through the preview renderer; INTEGRATED only when v1's plans flow through it into the rendered video; ₹0): section "PR 3" under "Task 046 · Part C (Economy)" below; with it every one of v1's 11 story pieces has a kit. The lesson seekh of entry 22 (PR #94; IMPLEMENTED by tests, measured on the resume's records; the live effect in the next lesson resume): notes carried on resume, notes-only and time re-measure findings minor, W-01 `answer codes?` narrowed, सफर, and the canvas section takes `--chapter-map` (bullet "The lesson resume" under "PR 2, addition").** Earlier the same day, **the Money chapter: the proof before the real run is complete (Section 1: 20 of 20 pages, 95 of 95 concept items with a checked real-world example; Section 2: 93 of 93 examples run before the term, 7 of 18 scripts pass after the words seekh and the lesson resume; ₹0 in all); the chosen video is v1 ("Money क्या है, और हमारे कौन-से काम करता है?"); next PR 3, the bank kit for v1's bank pieces → canvas plans by BIE on the VM → render in CI → ≤ 720p review copy and page → STOP for Navin's verdict; the lesson seekh (notes carried on resume, notes-only and re-measured-time findings minor, W-01 `answer codes?` narrowed) in its own PR (section "Task 046 · Part C (Economy)", bullet "The lesson resume").** Earlier, **27 October 2026, the Money chapter under Navin's real-world rule: Section 1 complete (20 of 20 pages, the map, 95 of 95 concept items with a checked real-world example; ₹0); Section 2: the plan passes at round 0 after the plan seekh, 18 scripts written with 93 of 93 examples run first (S2-08), 1 of 18 scripts passed, 17 failed mostly on everyday money words the list lacked → seekh `simple_hindi` 2026-10-27.2 (192 words) and W-01 source-packet phrases (`tests/test_task046c_money_words.py`); then a lesson resume.** Earlier, **the first Money lesson run: the plan failed on the Codex checker's demand for the teaching inside the plan (0 code problems; 20 content findings), no script written; seekh → BIE: a plan prefix, the plan's own checklist and structure-only blocking (`tests/test_task046c_plan_review.py`; the same plan passes at round 0 on replay); the lesson runs again after the merge.** Earlier, **the Money chapter read under Navin's real-world rule (VM job `t046c-money-understand-c`; INTEGRATED for Section 1: 16 of 20 pages and the map passed, all 102 economics concept items carry a checked real-world example; nothing ACCEPTED before Navin reads MAP.md's table; ₹0)** and the seekh from it (the checker asked for the example where the rule does not; a last-round slip gets one more round; section "PR 2, addition", last bullet; `tests/test_task046c_page_review.py`); the lesson job runs on the VM. Earlier, **seekh from the Money chapter's baseline map (IMPLEMENTED by tests, measured on the baseline's own three reviews, ₹0):** the map reviewer's wording findings on `core_explanation`, `notes` and `exam_focus` no longer fail a map whose structure passed (section "PR 2, addition", last bullet; `tests/test_task046c_map_review.py`); the baseline run `t046c-money-understand-b` passed 20 of 20 pages and failed its map after 3 rounds with 0 code problems; replayed under the seekh it passes at round 1. The new-rule run `t046c-money-understand-c` is on the VM. Earlier the same day, **27 October 2026, Task 046 Part C PR 4, render speed (IMPLEMENTED and measured on this machine; the CI chunk pipeline passed on the kit fixture in PR #86, merged at `8612d724` with every check green; ₹0):** section "PR 4" under "Task 046 · Part C (Economy)" below; the toolbox core lane passes (158 tests, 8 new in `tests/test_task046_render_speed.py`), the Task 045 lane passes. PR #82 (PR 1) is red on `demos (2)` for the GMT relief server, not for its own change: F-13d diagnosed and fixed in PR #83 (the asset cache was never saved: a path with `..`). Earlier the same day, **PR 2, the director's canvas and world modes (IMPLEMENTED offline with the fake maker; no live plan written yet; nothing INTEGRATED, nothing ACCEPTED; ₹0):** section "PR 2" under "Task 046 · Part C (Economy)" below; the toolbox core lane passes (150 tests, 13 new in `tests/test_task046_canvas_director.py`), the Task 045 lane passes. Earlier the same day, **PR 1, the kit inside BIE (IMPLEMENTED by tests and by the preview renderer on the kit's own test fixtures; nothing INTEGRATED until the real chapter's plans flow through it into a rendered video; nothing ACCEPTED before Navin's verdict; ₹0):** section "Task 046 · Part C (Economy)" below. The toolbox core lane passes (137 tests, 28 new in `tests/test_task046_canvas.py`), the Task 045 lane passes (464 tests, both passed-output sets unchanged). The economy PDF is not in the repo yet: Navin uploads it, then it goes to `blindtest-inputs`. Earlier, **26 October 2026, one-shot test (section "Task 046 · One-shot quality test"):** both routes made and on the review page. LOOK-01 (free Google key, against a written description of the benchmark): **Route 2 7.0 of 10, “same class”** (a Codex still, 4 of 4 images in 2 minutes on the ChatGPT plan, ₹0, moved in 2.5D by BIE code in about 3 minutes); **Route 1 5.3, “close”** (Blender, 203 s per frame, 7.6 machine-hours for the shot, ₹0; biggest gap: no wet translucency). Waiting for Navin's verdict. Earlier: **26 October 2026, Navin's verdict on Task 046 Part B: rejected.** “Part B ke dono routes ki video benchmark se bilkul mel nahi khati, reject. Part C shuru mat karo. PR #75 merge mat karo jab tak Navin agla faisla na de.” Both review copies (route A and route C) do not match the benchmark at all. Status stays IMPLEMENTED, not ACCEPTED; PR #75 is not merged; Part C is not started; BIE waits for his next decision. What was built and measured: **26 October 2026, Task 046 Part B, the blocks, the composer and the benchmark render (IMPLEMENTED; the demo clips and the segment render are made by CI; nothing ACCEPTED until Navin's verdict):** 18 blocks as code in `bie/brain/video/blocks/toolbox/` (`benchmark.tsx`: one three.js world per scene with a timeline of shots: `cell_sheet`, `particle_flow`, `focus_glow`, `organ_zoom`, `leader_label`, `camera_path`, `cutaway`, `exploded_view`; `grammar.tsx`: `kinetic_caption`, `board_build`, `mnemonic_card`, `concept_arrow`, `split_compare`, `scale_compare`, `flow_arrows`, `graph_plot`, `timeline`; `equation_steps` already in `maths.tsx`), 17 demo clips in the toolbox lane (batch 1, group `bench`, 1280 × 720, each checked against the rules it serves on its stills: dark field, caption band, accent on screen, labels lit, motion), the L4 clips on a procedural Earth wedge with a bar magnet (Navin's note); `bie/brain/video/compose.py` turns the director's shot list into a VideoSpec (one world layer per scene, a kinetic caption per clause, boards, cards, split screens, scale bars and reason arrows as panels, credits last; said = shown checked on the spec); `voice.py` the eSpeak NG placeholder (one WAV per beat drives the timing; the real voice is Task 047); `frame_checks.py` reads the rendered frames (B-03, B-08, B-10, B-11/VG-09, VG-01) into the 24-rule table with frame numbers; `tools/render_video.py` composes, renders in chunks through the preview renderer (Chromium + SwiftShader + ffmpeg, the same blocks real Remotion renders), joins, muxes, measures (render seconds per second of video, machine minutes, rupees at the list price), reports, and renders a 10-second sample again with real Remotion (the bridge); route C: `bie/toolbox/blender/cell_sheet.py` builds every family member (cilia, microvilli, layers, domes, keratin, a duct) and the same block draws the glTF by `data.models`; the workflow `.github/workflows/task046-benchmark.yml` renders v3's family segment (part c07.1: 76 shots, 12 members, about 5.6 minutes with the placeholder voice) at 1920 × 1080, 30 fps, both routes, and pushes the review copies, the cost table, the rule table and the shot list to `blindtest-results:runs/t046-v3-benchmark/`. **VM job 1 done:** v3 passed with the five W-01 beats rewritten (`docs/evidence/task046-director/W01.md`, SEEKH_LOG entry 12); the segment renders that script, and the composer refuses a plan the director blocked. **Benchmark run 40298550697 (this PR):** route A 27.2 render seconds per second of video (153 machine minutes, ₹103 at the list price, billed ₹0), route C 30.1 (169 minutes, ₹114); 77 shots, 337.6 s, L5a 93.6 %, one change every 4.59 s; rules A 14 pass / 2 partial / 2 fail (B-10 soft glow, B-03 a label part missing in 4 shots), C 15 / 2 / 1 (B-10); the real-Remotion sample gives the same frames; review copies on `blindtest-results:runs/t046-v3-benchmark/`. Earlier, **Part A**: **26 October 2026, Task 046 Part A, the code director (IMPLEMENTED offline; checked by tests on the real v3 script; nothing rendered, nothing ACCEPTED):** Navin's decisions recorded in his words (ROADMAP 046 and the section below); `docs/vision/VISUAL_LEVELS.md` + `rulebook/visual_levels.json` (L1 never, L2–L5a shot levels, L5b a planning error; **the level rule has two stars, Navin 26 Oct 2026:** A, chapter target 90–99 % of videos with their main level at L3+, a target and never a blocker; B, the level is per shot, L2 only with its reason, no video blocked for its level; the pace is the visual-change rate, micro 3–5 s, engineering/physics 10–20 s, VG-01 checks it; benchmark B-01 and S3-06 now say 3–5 s); `rulebook/visual_grammar.json` (VG-01…VG-11 locked for director and visual, W-01 for lesson and director, the W-01 word list in Hindi, Hinglish, English and mixed forms); `soul.wording_problems` wired into the script checks with a RULE_CHANGES entry (the two passed-output sets still pass: W-01 reports as a changed rule); every capability carries `default_level` and `blocks` (42, validated; grammar blocks listed); `bie/brain/shots.py` + `tools/shot_list.py`. **Offline proof on v3** (`docs/evidence/task046-director/`): 161 shots for 53 beats (one per spoken clause), 624 s, 6 scenes (one per part), 0 cuts, world `cell_sheet_3d`; capabilities: cell sheet 94, particle flow 29, organ zoom 11, board 11, split screen 10, mnemonic card 5, family tree 1; **main level L5a (86.8 % of the seconds; L3 13.2 %), chapter report 1 of 1 videos at L3+ (target met)**; pace: one visual change every **4.14 s** after the director added 68 camera moves (7.52 s before; micro target 3–5 s); 24-rule table: 14 pass, 4 partial (B-01 18 clauses over 6 s, B-02 member seconds, B-11 and VG-09 decided by the render), 5 n/a, **W-01 fail: 5 beats of v3 point at the book** (b22, b24, b29, b30, b36: "Book short cylindrical कहती है", "Book … बताती है", "book … की बात करती है", "Printed location है", "book waterproof कहती है"), so v3 is blocked from rendering until VM job 1 rewrites those five beats (the other 10 videos: 11 more hits, in v4, v5, v7, v8, v9; not touched by job 1). Cost ₹0. Earlier, **25 October 2026, Task 046a-L licence gate (IMPLEMENTED; not used on a real book yet):** one policy file (`bie/toolbox/licence_policy.json`, version `2026-10-25.1`, Navin's words in it) read by every licence decision through `bie/toolbox/licence.py`; the gate `lesson_licence_check` runs in the visual section, the game builder, the Scene IR asset resolution and the compiler's asset bundle, and `AssetLibrary.require_lesson` is the hook for Task 046's director; refused for lessons: Z-Anatomy (CC BY-SA); needs Navin: India Code, Hipparcos, BodyParts3D, SRTM15+ relief, India's political boundary; 9 proof clips marked "internal proof, not for lessons"; section below. Earlier, **25 October 2026, Task 046a batch 3 (IMPLEMENTED, demo proven; nothing used on a real book yet):** 21 more registry entries (80 in all): Natural Earth 1:10m with India's own boundary view and Shapely, Wikimedia Commons and Openverse, the World Bank API, Chart.js, Vega-Lite and Vega, Plotly, Mermaid with ELK, dagre, India Code (bare acts as data), the Supreme Court judgments dataset with pyarrow, PsychoPy, Indic NLP and indic_transliteration, Noto Sans Devanagari; 16 more proof clips (51 in all); 40 of 42 capabilities have a tool; the UGC NET (86 subjects) and GATE (30 papers) map; section below. Earlier, **25 October 2026, Task 046a batch 2 (IMPLEMENTED, demo proven; nothing used on a real book yet):** 28 more registry entries (58 in all): Schemdraw, Lcapy, ngspice, python-control, scipy.signal, PyNite, sympy.physics, CoolProp, CadQuery, scikit-fem, GMT and PyGMT with the SRTM15+ relief, ObsPy, pyGPlates with the Müller 2019 plate model, the USGS catalogue, Natural Earth, Astropy, Skyfield with JPL DE421 and Hipparcos, NASA images, AeroSandbox, JSBSim; FEniCS and OpenVSP blocked with their reasons (no PyPI build); 15 more proof clips; section below. Batch 1 merged with PR #69 (`6e3f2c22`, all checks green). Earlier, **25 October 2026, Task 046a batch 1 (IMPLEMENTED, demo proven; nothing used on a real book yet):** `bie/toolbox/` with the registry (30 tools, all demo proven), the capability vocabulary (42: Navin's 41 + `split_compare`; 16 subject families), the resolver and the missing-capability log; the web path (BIE blocks for Remotion with three.js, KaTeX, D3, 3Dmol.js, Mol*, matter.js, cannon-es) and the offline path (Blender headless → glTF, Manim); 20 silent proof clips made by BIE code, and the bridge proof (the same 3D clip through real Remotion 4.0.536 and through the preview renderer: same frames). Section below. Earlier, **25 October 2026, closing runs (PR #67 merged at `26b5ff24`, all checks green):** the ₹0 test job (`t045-free-reviewer-smoke`, tissue page 1) proved the reviewer route from the VM: every Google call via `direct`, model `gemini-3.8-flash`, no AICredits call (the map review: 9,908 input, 2,072 output tokens of which 1,367 thinking). The lesson resume `t045-tissue-lesson-finish` (3.7 minutes) reused the plan and 9 scripts and continued v5 and v9 from their last answers with no maker call: **both passed at round 0, so 11 of 11 videos pass** (116.5 spoken minutes, dohraav 0 of 500, 69% of beats open a term, a why or an example). Reviewer: v9 0 findings; v5 passed with one time note (18.7 spoken minutes against the 18.4 guide, inside the code's 3% tolerance). Cost: ledger estimate ₹7.13 + ₹1.63 at the list price, **billed ₹0** (Google free tier); Codex plan 8% of the week. Readable scripts: `blindtest-results:runs/vm-t045-tissue-lesson-finish-brain-lesson/scripts/v5.md` and `v9.md`. **25 October 2026, Navin's verdict:** he read old v2 (epithelial, `vm-t045c-tissue-lesson-v9`) against the new epithelial script (new v3, `vm-t045d-tissue-lesson-resume2`; the new plan splits videos differently, so topics are compared by topic, not by video id) and chose to **go forward with the NEW scripts**. Task 045 is complete for now; **045e (completeness and full sentences) is not done now**: if, after the one-button software, a real book's output shows a gap in any section (teaching, video, narration, notes), Navin opens a new improvement task then. The reviewer stays a permanent part of BIE. His observations, for the record only: the new scripts use more examples and analogies; the old ones had fuller sentences and more completeness; some new sentences feel clipped. No explanation was locked in the library (that stays his call). **Reviewer key (Navin's decision):** his free Google AI Studio key `GEMINI_API_KEY` is in `/etc/bie/bie.env` on the VM (the AICredits key stays there unused); VM jobs use `reviewer google`, `models google=gemini-3.8-flash`, `routes google=direct`; free tier: sample content only, never student data (Navin accepted this). Seekh PR (branch `task045-free-reviewer`, SEEKH_LOG entry 11): a review call gets its own output cap of 12,000 tokens (measured; v5's runaway review hit 32,000), Google's per-minute free-tier quota is waited out instead of read as an empty wallet, and `tools/codex_vm.py status` shows which Gemini keys are present and the default route. Then a ₹0 test job proves the route from the VM and a lesson resume finishes v5 and v9. **25 October 2026:** seekh PR #64: a failed script continues from its last answer (round 0, no maker call), 30 more everyday words and oblique forms, Navin's contrast and memory openings, and **the cost guard now prices a billed failed call** (SEEKH_LOG entry 10). Correction to the line below: v5's truncated answer was the **reviewer's** (ledger `lesson:script-v5:r3:review`, `aicredits:truncated: output reached max_tokens=32000`); the maker's round 3 passed every code check. That review is billed (estimated ₹40–48) but the ledger counted ₹0, so Task 045d is about **₹205 estimated, not ₹161.59** (about ₹5 over Navin's ₹200); the AICredits dashboard has the real bill. v5 and v9 are both clean by code. **24 October 2026, end of day:** after PR #65 (`1c6c349d`, converging rounds) the third script run passed v2, v4 and v8: **9 of 11 videos pass**, **dohraav 0.0%** (0 of 500 judged beats; before Task 045d 28.7%), opened 67.2%. v9 is clean by code and waits for one Gemini review: the run stopped on `402 Insufficient Balance`, **the AICredits wallet is empty (Navin: add credits at aicredits.in/dashboard/billing)**; v5 (128 beats, 18.7 min) hit the 32,000-token output limit in its patch round (next seekh: smaller patches for long scripts or shorter videos in the plan). Task 045d Gemini ₹161.59 of ₹200. Old v2 against new v2: `V2_SIDE_BY_SIDE.md` in `runs/vm-t045d-tissue-lesson-resume2-brain-lesson/`. Nothing ACCEPTED until Navin's verdict. Earlier: job B resumed after PR #62 (`78e0cf6a`; F-12 harness fix PR #63 `ea8ccaa5`): **6 of 11 videos pass** (v0, v1, v3, v6, v7, v10; reviewer 0 blocking), dohraav **0.4%** (2 of 511), opened 64.4%, Gemini ₹12.01; v2, v4, v5, v8, v9 fail by code with 1–4 residues after 3 ever-smaller rounds. Seekh: converging rounds in the runner + 11 words (PR #65), then the last resume with the remaining ₹62.85. Task 045d Gemini so far ₹137.15 of ₹200. Earlier: the Task 045d rerun is done through both steps. Understanding: 14 of 14 pages and the map passed under the new rules (jobs A, resume2, resume3; Gemini ₹100.28; the reviewer found 0 blocking problems; code sent 9 pages back once for textbook Hindi). Script (job B, Gemini ₹24.86): plan passed, **dohraav 28.7% → 1.9%** (155 of 540 → 9 of 481 judged beats; 27.6% → 1.0% with the job B markers), opened 28.3% → 60.9%; 4 of 11 videos passed, 7 failed by code after 3 rounds (everyday words the list lacked, a few restating beats, 1–2% over time); seekh in PR #62 (SEEKH_LOG entry 9), then job B resumes with the rest of the ₹200 (₹74). Old v2 against new v2: `V2_SIDE_BY_SIDE.md` in the job B run folder. Nothing ACCEPTED until Navin's verdict. Earlier that evening: PR #60 (Task 045d) merged at `ce0e3491`, all checks green. Job A (`t045d-tissue-understand`, cap ₹80) ran 14.2 minutes and **stopped on the AICredits key budget** (`402 API Key Budget Exceeded`; Gemini ₹13.51): page 2 passed, 13 pages wait. **Blocked on Navin: raise the key's budget at aicredits.in/dashboard/keys**, then the prepared resume job (`t045d-tissue-understand-resume`, cap ₹70, page 2 reused) runs, then job B (script). Seekh from page 2 (SEEKH_LOG entry 8): plain meanings in textbook Hindi (ऊतक, कोशिका, उपकला) → `technical` block in `simple_hindi.json` 2026-10-24.1, checked in the unpack (S1-15) and the script (S2-04). Earlier the same day: Navin read the 11 tissue scripts and gave his verdict: they restate the book ("epithelium absorptive aur secretive surfaces par milta hai") instead of opening it. Measured with the new detector: 155 of 540 judged beats (28.7%) only restate, 35 topics open without a question, 17 clipped note-sentences, 4 duplicate recaps (SEEKH_LOG entry 7). Task 045d builds the answer into BIE for every subject (section below); IMPLEMENTED offline, nothing INTEGRATED until the rerun, nothing ACCEPTED until Navin's verdict on old v2 against new v2. Earlier: job 1 (14 pages, map) and job 2 (plan, 17 scripts) finished on 23 October 2026: 14/14 pages, map passed, 15/17 scripts passed; Gemini ₹165.55 of ₹250. Navin's decisions on the run are recorded below; the fixes (length rule, prerequisite video and map trim, bracket quality, Section 1 typo and basis rules, caching probe) are merged with PR #53 (`0ca5763d`, all checks green); rule CI-2 with PR #54; the F-11 native-render fix with PR #55 (`cb198dff`, Navin's yes). Caching probe done (run 40007533161): Gemini 4 Argon through AICredits gives no prompt-cache discount (a repeated 5,246-token prefix: 0 cached tokens, 0 cache writes), AICredits billed ₹2.43 against a ledger estimate of ₹2.24. Job 3 (`t045c-tissue-lesson-v2`, 34.6 minutes, Gemini ₹78.17): the map's prerequisites trimmed 30 → 8, plan with v0 and 10 topic videos, 6 of 11 scripts passed; the 5 failures were a loop between the time rule and a reviewer that still asked for optional outside questions (SEEKH_LOG entry 4). The fix merged with PR #57 (`0dd27ec2`); the resumed job passed 4 of the 5 (reviewer: 0 blocking findings), so 10 of 11 videos pass, 113.9 spoken minutes, Gemini ₹99.56 of ₹150 (SEEKH_LOG entry 5). v9 failed by 0.1 minute after its patches cut recap beats; that fix merged with PR #58 (`2d1bafa4`) and v9 then passed. **The tissue script step is complete: 11 of 11 videos pass** (113.6 spoken minutes: v0 7.4, topic videos 106.2 against 84–112); Gemini for the rerun ₹106.43 of ₹150. Final folder: `blindtest-results:runs/vm-t045c-tissue-lesson-v9-brain-lesson/` (SCRIPT.md, scripts/v0.md … v10.md). Waiting for Navin's verdict on the scripts (SEEKH_LOG entry 6). The other five chapters wait. Task 044b is not started |
| Next task | **STOP for Navin's verdict on v1** (the review copy and the page): is this the direction for the economy chapter, what to fix first, any part in the wrong mode (B default, C for story parts), which examples to lock. After his verdict: the fixes as seekh PRs, then the rest of the Money chapter's videos the same way (v0, v2–v17; 5 scripts still fail on reviewer content findings: W-01 phrasing in v2 and v4, outside sourcing in v10, example-before-name order in v11 and v12), the voice (Task 047). Small open item: the canvas section's preflight asks for a reviewer route it never calls (a job without `reviewer codex` stopped on the VM's default Google route). Earlier: PR #94 (the lesson seekh) green and merged → canvas plans by BIE on the VM (`--section canvas`, Codex, ₹0) → render (`BIE Task046c Render`, full MP4 in CI artifacts) → ≤ 720p review copy on `blindtest-results` and the review page → STOP for Navin's verdict; alongside, the lesson seekh PR and the lesson resume `-d` for the 11 failed scripts. Earlier: PR 1 (#82) green and merged → PR 2 rebased, pushed, green and merged → PR 3 world kits for the chosen video's places → PR 4 render speed (parallel chunks in CI joined to one MP4, static layers pre-drawn, no per-frame SVG filters; a 5–8 minute video in under 60 minutes wall-clock, measured) → the real video from Navin's sample economy chapter (plans by BIE only; silent with captions; full MP4 in CI artifacts, ≤ 720p review copy on `blindtest-results`, the review page) → STOP for Navin's verdict. Still open for Navin: the economy PDF upload; the one-shot verdict (PR #76 stays a draft); the toolbox clips; the licence decisions (India Code, Hipparcos/ESA, BodyParts3D, citation-only data, India's boundary, the Remotion licence, OpenAI image output for lessons) |
| Canonical main | `f99b77a6` (PR #93: PR 3, the bank kit) on `f929d5a5` (PR #92: docs, the proof's numbers and the chosen video) on `d265dc90` (PR #90: the everyday words of money and the W-01 source-packet phrases; PR #91 `abeb70b0` F-16 skyfield files in the shared asset cache; PR #89 `f03c9208` plan review; PR #88 `182c9b01` page review; PR #87 `995c808b` map review; PR #86 `8612d724` render speed; PR #85 `78a9a721` PR 2 and Navin's addition; PR #81 `d7ce8388`: F-14b, Codex image calls keep the code-mode host on, Navin's yes; PR #80 `4128cbdd` F-14; PR #77 `aa8d6519` VM image and look jobs; PR #79 `2c6c2fc5` F-13c + F-11 toolbox lane; PR #78 `c4375064` F-13b; PR #74 `39e3430e` Task 046 Part A) |
| Keys | Never the Anthropic key. GPT API key off. Gemini key (AICredits) for the checker; it may call only `google/gemini-4-argon`. GPT only through ChatGPT Pro, signed in with Codex on Navin's machine (Hostinger KVM 2, Mumbai). On the VM, from 25 October 2026, the checker is Navin's free Google AI Studio key `GEMINI_API_KEY` in `/etc/bie/bie.env` (direct route, `gemini-3.8-flash`); the AICredits key stays there unused (a job can still choose it with `routes google=aicredits`). Since 24 October a free Google AI Studio key is the GitHub secret `GEMINI_API_KEY` (Navin's choice for now, sample content only, never student data); it serves GitHub Actions runs only and wins over AICredits there: `gemini-3.8-flash` answers (smoke run 40114580580), `gemini-4-argon` gives 429 quota and `gemini-3.1-pro` 404, so a run that uses it passes `models=google=gemini-3.8-flash` |

## Task 046 · Part C (Economy), PR 1: the kit inside BIE (27 October 2026)

Navin's decisions, 27 October 2026, in his words (also in ROADMAP 046):

- **"B DEFAULT KE SATH KAHANI WALE HISSON MEIN C."** Every economy part is a build-up canvas with L3 touches (B) by default;
  a story part with actors in a place (a shop and its buyers, a bank and its borrowers, a factory and its workers, a port, a
  farm) is an L3 world (C). A B shot is reported as "L2 + touches", a C shot as L3; the 90–99 % L3+ target stays a target,
  never a blocker (the two-star rule of 26 October).
- Lesson assets: CC0 and CC BY only (the 046a-L gate); W-01 holds; lesson content (scripts, plans, scenes, frames) is made
  only by BIE, never by hand; keys and the cost guard as CLAUDE.md. Maker Codex on the VM at ₹0, reviewer on the free Google
  key; any paid call is capped at ₹50, listed in the report, and Claude asks before more.
- The kit counts as INTEGRATED only when the real chapter's plans flow through it into a rendered video; nothing is ACCEPTED
  before his verdict; `batches/`, `historical/`, `backups/`, `docs/evidence/` untouched; reference videos never enter the repo.

Built in PR 1 (branch `task046c-kit`; IMPLEMENTED by tests and by the preview renderer on the kit's own test fixtures; cost ₹0,
no AI call):

- **Blocks.** `bie/brain/video/blocks/toolbox/canvas.tsx` (`canvas_build` + `curve_story`) and `world.tsx` (`world_scene`),
  imported by the toolbox bundle's `index.ts` with the other toolbox blocks (`../registry`, `./common`). The kit's own subtitle
  drawing is gone: **captions are drawn once**, by the core strip in `blocks/index.tsx` (a dark strip under white words, so they
  read on the paper canvas and on the dark world alike); every compiler returns the scene with its `captions`, and a caption
  holds through a pause shorter than 1 s until the next line starts (no flicker between beats; the tail after the last beat
  shows none). `timing.build`, both compilers and `squeeze` take a `lead_in` (the 0.4 s silence before the first beat for a
  lesson; a proof clip starts at once).
- **Compilers.** `bie/brain/canvas.py`: a director's plan (what, in which grid cell, on which spoken word) → the scene and a
  report (mode B or A, level "L2 + touches" or L2, elements, longest still, change rate, problems, advisories); the layout, cue
  timing and first-try checks are code: unknown kind or cue word, two elements sharing cells at the same time, text that does
  not fit at ≥ 24 px, a missing reference, more than 16 visible, a still over 15 s (blocking) or 7 s (advisory); `stubs` groups a
  video's beats exactly as `shots.scenes_of` (so canvas scenes line up with the code director's scenes), `credits_scene` draws the
  closing credit card, `video_spec` wraps scenes for the renderer, `trim_plan` and `squeeze` make proof clips.
  `bie/brain/video/world.py`: a world plan → `world_scene` (mode C, level L3; a world needs its place and camera keys in time
  order); `KITS` lists the places a kit exists for (`shop` so far) and `kit_for` finds a part's place by its words.
- **The danda bug.** `timing._norm` counted the whole Devanagari block as word characters, so a sentence's last word stayed
  glued to its danda ("CPI।") and a cue on that word was never found: it landed silently at the beat's start. Now the danda and
  double danda are punctuation, `timing.has_word` is the one word matcher, and `director.word_in` uses it too (its own copy of
  the same regex is gone).
- **Rulebook.** `rulebook/canvas_profile.json` (`canvas_profile@2026-10-27.1`): CV-01…CV-12 as locked rules for the director
  and the visual section, the limits the compiler enforces (min font 24 px, ≤ 16 visible, still ≤ 15 s blocking and 7 s
  advisory, a change every 6 s as the target) and the measurements they were set from (20 Indian-economy reference videos
  measured by code: a visual change every 5.0 s median, 7.5 s p90). The director card `rulebook/canvas_director_card.md`
  (PR 2 puts it in front of the maker).
- **Icons as toolbox sources.** `bie/toolbox/icons.py` with the index `bie/toolbox/icons/index.json.gz` (schema `bie.icons/1`,
  4,213 icons: Twemoji 1,939 colour icons without skin-tone variants, Font Awesome Free 2,274 solid and regular line icons
  with their search terms; no brands, CV-11): `search`, `check_ids` (a plan naming an unknown icon is refused before any
  render), `copy` (Font Awesome paths take the ink colour) and `add_to_library` (the icons as assets with the CC BY credit
  fields, so `lesson_licence_check` passes them and `lesson_credits` writes their lines). Files come from a local checkout
  (`BIE_TWEMOJI_SVG`, `BIE_FONTAWESOME_SVGS`) or one by one from the pinned tags on GitHub (jdecked/twemoji `v16.0.1`
  `assets/svg`, FortAwesome/Font-Awesome `7.3.1` `svgs`) through `sources.cached`, never into git. Why GitHub and not npm:
  `@twemoji/svg` on npm is a third-party repackage missing 30 of the index's files; the official tag has every file. Registry
  `2026-10-27.1` (83 tools): `twemoji` and `fontawesome-free` (asset sources, CC BY 4.0, adapter `bie.toolbox.icons`, batch 3,
  demo proven) and `bie-econ-blocks` (js_lib, `canvas_build, curve_story, world_scene`). Credit lines: "Twemoji graphics by
  Twitter, Inc and other contributors, CC BY 4.0" and "Font Awesome Free by Fonticons, Inc., CC BY 4.0"; the credit roll lists
  every CC BY credit the video used.
- **Proof clips** (batch 3, `tools/toolbox_demos.py`): `econ-canvas-demand-pull` (B: shop, price, buyers, goods and coins
  flowing), `econ-curve-phillips`, `econ-price-chain` (Twemoji and Font Awesome icons), `econ-table-real-gdp` (tree and table),
  `econ-world-demand-pull` (C: the 2.5D street); each is a kit fixture in `tests/fixtures/task046c/` (the kit's own hand-written
  test plans, not lesson content) cut to its first beats and fitted into 4.4–4.8 s through the same compilers a lesson uses.
- **Tests and lanes.** `tests/test_task046_canvas.py` (28: timing, canvas, world, icons with fake checkouts and a fake
  fetch, registry, blocks, demos) in the toolbox core lane (`toolbox.yml`, 137 tests); the Task 045 lane (464 tests) and both
  passed-output sets still pass (no script check changed; the rulebook version grew by `canvas_profile`).
- **Rendered here through BIE's preview renderer** (Chromium, the toolbox bundle built by esbuild from the ported blocks):
  four stills of every fixture (demand-pull canvas with and without touches, Phillips curve, price chain, real GDP table), the
  world and the credits card, 28 stills, every element, icon and the caption strip drawn; the five proof clips rendered by
  the demo runner with their frame checks (not blank, moves) and 3–5 s lengths. Nothing of this is lesson content.

Not in PR 1 (the next PRs): the director's canvas and world modes with the AI plan step and the code-check loop (PR 2), world
kits for the chosen video's places (PR 3), render speed (PR 4), the real video from Navin's sample economy chapter (after his
PDF is uploaded and put on `blindtest-inputs`).

### PR 2 · the director's canvas (B) and world (C) modes (27 October 2026)

Built on branch `task046c-director` (IMPLEMENTED offline with the fake maker, by tests; no live plan written yet; the first
real numbers come from the chapter run; cost ₹0):

- **`bie/brain/canvas_director.py`.** For a canvas subject (`canvas_profile.json` `families`: economics, commerce and
  management; geography, history and polity, by `shots.subject_family`) every part of a passed script becomes one plan:
  `mode_of` picks **C** when the part's words name a place that has a world kit (`world.PLACES`: shop, bank, factory,
  port, farm; `world.KITS`: shop so far) and **B** otherwise, and a place without a kit goes to `missing_kits` (the
  missing-capability line). A part longer than 12 beats becomes two or three canvases (CV-10). The maker gets the director
  card (`rulebook/canvas_director_card.md`, or `world_director_card.md` for C), the CV rules through the rulebook
  (section `canvas`), an icon menu of 110 index ids (the maker has no search tool at run time; any other id is refused
  with the nearest matches), the part's beats, items and on-screen hints, and answers a strict JSON plan (every field
  present, unset = "" / 0 / []); `plan_from` / `world_from` turn it into the kit's plan, `check_plan` compiles it and a
  refused plan goes back as the exact code error (`[code] cue word 'nowhere' is not in beat c1: …`), **no reviewer round
  for layout**. `run_canvas` writes `plans/<part>.plan.json`, the icons into the asset library with their credits,
  `video_specs/<video>.json` (scenes in part order, captions, the credits card; the same place the visual section writes,
  behind the same licence gate), `canvas.json` (per part: mode, level, status, rounds, `first_try`, elements, longest
  still; per video: `first_try_passes`, rounds, modes, credits; `missing_kits`) and `CANVAS.md`.
- **The run tool and the VM:** `tools/run_brain.py --section canvas --from-run <run> [--videos v1] [--render]` (cost
  estimate section `canvas`, assumed $0.10 a page until measured); the VM job `section: canvas` with `from_run` and
  `videos`; maker Codex at ₹0, reviewer unused for layout.
- **The fake maker** (`bie/brain/fake.py`) answers canvas and world plans offline, so the run, the tool and the VM job
  are tested end to end without a key: 13 tests in `tests/test_task046_canvas_director.py` (modes and places, the strict
  answer → plan, exact refusals, the world plan, splitting a long part, the step's card and menu, a run that writes plans
  and specs and counts first-try passes, a refused first answer costing a round with the error in the record, the bank
  story falling back with its missing kit, a non-canvas subject left to the shot-list director, the run tool on a run
  folder, the VM job).
- Rulebook `canvas_profile@2026-10-27.2`: `families` and the `canvas` section on CV-01…CV-12.

### PR 2, addition · real-world application for economics (Navin, 27 October 2026)

**Navin's words:** "in videos se economics padhane ke tarike mein ek cheej daalni hai ki economic concepts ko explain karne ke
liye real world mein apply karke samjhao, jaise demand pull inflation wale concept ko dukandar, bazar, log, sugar wale
example se samjhaya tha." Put into the director/script PR as he asked (not into PR #82); IMPLEMENTED offline by tests, ₹0;
INTEGRATED only when the Money chapter runs through it (the proof below); nothing ACCEPTED before his verdict.

- **The method (rulebook, versioned):** `teacher_examples.json` 2026-10-27.1 adds `real_world_application` with his sugar
  shop paraphrased (3 packets at ₹50, buyers 2 → 12, the price ₹65, only 3 can buy; "isliye ise demand-pull inflation kehte
  hain"; then the book's definition; then where the learner meets it) and the slot's parts (a place, actors, real goods or
  money, numbers that change, the mechanism step by step, the term after the story). It reaches the page prefix
  (`PAGE_TEACHER_METHODS`) and the script prefix. `content_types.json` 2026-10-27.1 adds `real_world_example`: in a chapter
  of the economics family (`shots.subject_family`), every `definition`, `cause_effect` and `process` item carries the slot
  (`ContentTypes.needs_real_world`). `simple_hindi.json` 2026-10-27.1 adds 19 everyday words of a bazaar, bank or farm story
  (ग्राहक, खरीदार, दुकानदार, मंडी, किराना, बैंक, उधार, ब्याज, किस्त …) the list lacked. `vision-2026-10-21.json` 2026-10-21.14 locks
  **S1-16** (understand) and **S2-08** (lesson); the reviewer's checklist carries both.
- **The slot:** `unpack.real_world_example` = `{place, actors[], goods[], numbers[{what, before, after}], steps[{step,
  mechanism_link}], term_after, real_life_link}` (`soul.REAL_WORLD_SCHEMA`; the page schema is `bie.brain.understand-page/4`,
  the prefix `understand.read_page/4`; every other item leaves it empty). `MAP.md` gets the section "Real-world examples
  (S1-16)": per concept item, the example BIE chose in one line, today's check, the page's rounds and first try; `PAGES.md`
  and the script source carry the example's lines ("real world (run it first, with these numbers, then name the term) | …").
- **Code checks (no extra reviewer round):** `soul.real_world_problems` (S1-16, in `check_page` by the course's subject
  family): the place, an actor, the goods, at least one number whose digits change, two or more steps each with its
  mechanism link, the naming sentence, the real-life link; `soul.example_order_problems` (S2-08, in `check_script`): the
  beats that cover the item and carry the example's numbers come before the first beat that names the item's term (from
  `unpack.terms`), and such beats exist; `example_order_report` gives the per-item rows (`lesson_plan.json` per video
  `real_world`, quality `real_world.items` / `run_first`, the SCRIPT.md section "Real-world examples (S2-08)"). The reviewer
  prefixes say an economically wrong example (the wrong mechanism, numbers moving the wrong way, not at the level) is
  blocking. `regression.RULE_CHANGES` carries S1-16 and S2-08 (the tissue passed outputs are not economics; both sets still
  pass).
- **The director:** `canvas_director.story_split` makes the example's beats (they cover an item with an example and carry
  its numbers) their own STORY piece `<part>s` (the beats before and after stay canvases `<part>a` / `<part>b`);
  `mode_of(..., story=True)` takes the example's place first (C when a kit exists, else B with the user message
  `STORY_NOTE`: crowd, value and icon elements following the numbers) and logs a place without a kit by its own name
  (`petrol_pump` is a known place now; "world kit for a petrol pump"); `canvas.json` counts `story_parts` and
  `story_parts_in_a_world`.
- **The fake maker** fills the slot for economics concept items and opens such a part with the sugar-shop story beat (its
  numbers first), so an offline economics chapter passes Sections 1 and 2 on the first try. Tests: 15 new in
  `tests/test_task046c_real_world.py` (rulebook and prefixes, every S1-16 part named, `check_page` by family, the lines and
  the map rows, S2-08 good order / term first / no numbers / other subject, the director's story piece in a world and on
  the canvas with its missing-kit line, the offline Money chapter end to end with first-try counts, `check_script` catching
  a term named before its example on the real card); the toolbox core lane 165 tests, the Task 045 lane 479 tests
  (version pins moved: `read_page/4`, 11 methods, `vision@2026-10-21.14`, `simple_hindi@2026-10-27.1`).
- **The proof before the real run (item 4):** after this PR merges, the Money chapter's understanding runs again on the
  VM (the first run, under the old rules, is the "before"), then the script step; MAP.md and SCRIPT.md show per concept
  the example BIE chose with the check results and the first-try counts, and Navin reads them before the video. The VM
  job `t046c-money-understand` of 12:42 UTC (old rules) is the baseline for the measured effect.
- **The first Money run (VM job `t046c-money-understand`, old rules, 12:42–13:39 UTC, 43 minutes; `blindtest-results:
  runs/vm-t046c-money-understand-brain-understand/`):** 4 of 20 pages passed (pages 1 and 3 first try, 4 and 5 in two
  rounds), page 2 failed, pages 6–20 and the map stopped: `stopped: balance`, the free Google key answered **429
  RESOURCE_EXHAUSTED** on every call from page 6 on (15 refused calls) and again on the one-page probe `t046c-quota-probe` at
  13:52 UTC, so it is the free tier's daily quota, not a per-minute one (it resets at 07:00 UTC). Codex plan 1 % of the
  week; Google list price ₹9.50, billed ₹0; 165 items, 137 teachable, 381 teacher questions. **Seekh from it, in this
  PR:** (a) page 2 lost a round to "पदार्थ → substance" although the Money chapter never says "substance": the textbook-Hindi
  check (S1-15 in the unpack, S2-04 in a beat) now counts only the translations of terms the book itself uses
  (`hinglish.english_terms` of the page's text and items, of the chapter's items in a script; `technical_words(book_terms=…)`);
  (b) the records kept only 300 characters of a provider error, hiding Google's quota id: the maker, reviewer and ledger
  error texts keep 1,500. The rerun under the new rule (the proof) runs when the free quota is back, or on the AICredits
  Gemini route inside Navin's ₹50 cap for paid calls.
- **The baseline map and the seekh from it (VM job `t046c-money-understand-b`, 15:20–16:17 UTC, 56.8 minutes, Codex
  maker and Codex checker on the ChatGPT plan, ₹0; `blindtest-results:runs/vm-t046c-money-understand-b-brain-understand/`):**
  **20 of 20 pages passed** (4 reused from the first run; 16 made now: 7 first try, 7 in two rounds, 2 in three), 497
  items, 409 teachable, 1,284 teacher questions; **the chapter map failed after 3 rounds with 0 code problems in every
  round**: the Codex checker's 12 blocking findings were 10 on the wording of `core_explanation`, `notes` or `exam_focus`
  (the digital-rupee pilot date, "first banknotes" without "in Europe", legal tender against fiat, security features as a
  readout, reserve money not opened …) and 2 on structure (a prerequisite bundle wider than the direct need; RuPay as a
  prerequisite of MDR), and each round brought new wording findings on other concepts. The map is structure: a concept's
  `core_explanation` is a two-line summary for later sections, the lesson is written from the items and reviewed there. Seekh
  → BIE (branch `task046c-map-review`, `tests/test_task046c_map_review.py`, 8 tests): `understanding.connect_review_problems`
  counts only structural findings as blocking (`structural_finding`: items, relations, prerequisites, references, question
  links, teaching order; a finding naming both, or no field, blocks; a failed verdict naming no blocking finding still goes
  back once); wording findings stay in the record (`wording_findings`); the checker's prefix says so. Replayed on the
  baseline's own three reviews: round 0 keeps 1 blocking finding (the prerequisite bundle), round 1 keeps 0, so **the same
  map passes at round 1 (2 maker calls, 2 checker calls) instead of failing after 3 of each**. The new-rule run
  `t046c-money-understand-c` (S1-16, no reuse) was picked up by the VM at 16:17 UTC; its map, if it fails the same way, is resumed under this
  seekh (pages reused, map only), then the lesson job. The toolbox core lane passes (173 tests), the Task 045 lane passes
  (491 tests, both passed-output sets unchanged).
- **The new-rule run (VM job `t046c-money-understand-c`, rule S1-16, no reuse, 16:19–17:43 UTC, 84.2 minutes, Codex maker and
  Codex checker, ₹0, Codex plan 7 % of the week; `blindtest-results:runs/vm-t046c-money-understand-c-brain-understand/`):**
  **16 of 20 pages passed, the chapter map passed at round 1** (under the old map rule; its round-0 findings were again 4 on
  wording and 1 on structure), 457 items, 389 teachable, 371 unpacked, 1,305 teacher questions; **every one of the 102
  economics concept items carries its real-world example and passes the S1-16 code check on the first try** (MAP.md, section
  "Real-world examples (S1-16)": the example BIE chose per item, for example p001-i10 divisibility: kirana shop, buyer and
  shopkeeper, soap and a ₹100 note, the buyer's cash ₹100 → ₹70). Rounds, however, went up: 2 pages first try (baseline 7 of
  16) because the Codex checker sent 18 of 20 pages back at round 0 while BIE's code was clean on 18 of 20; pages 4 and 15
  failed on the checker (real-life links to Indian rupee practice without a page source; timeline "why" answers), pages 7 and
  12 on one code slip the maker made in the last allowed round (a block id, a type note). **Seekh → BIE (branch
  `task046c-page-review`, `tests/test_task046c_page_review.py`, 10 tests):** (a) 24 of the checker's 53 first-round blocking
  findings asked for a worked example on timelines, classifications, comparisons and fact lists, where S1-16 asks for none:
  `understanding.page_review_problems` (the runner now hands the maker's answer to a review that needs it) counts such a
  finding as minor in an economics chapter and passes a page whose blocking findings were all such; the checker's prefix says
  so. Replayed on the run's own reviews: 79 → 53 reviewer problems counted over all rounds, first-try pages 2 → 3, page 8
  passes at round 0 instead of 1; the rest is measured live on the resume. (b) The first code problems after code-clean rounds
  (a slip while fixing the checker's findings) count as converging, so the step gets one more patch round instead of failing:
  pages 7 and 12 would have had it. Next: after this PR merges, the resume `t046c-money-understand-d` (16 pages reused, the 4
  failed pages and the map); the lesson job `t046c-money-lesson` already runs on the 16 passed pages' map. The toolbox core
  lane passes (191 tests), the Task 045 lane passes (501 tests, both passed-output sets unchanged).
- **The first Money lesson run (VM job `t046c-money-lesson`, 17:48–17:59 UTC, 10.8 minutes, Codex maker and Codex checker,
  ₹0; `blindtest-results:runs/vm-t046c-money-lesson-brain-lesson/`): the plan failed after 3 rounds with 0 code problems in
  every round, so no script was written.** The plan itself was in order (18 videos: v0 with the 25 prerequisites, v1–v15 topic
  videos in the map's order, v16–v17 practice; every concept in a video; the minutes within S2-01), but the Codex checker
  judged it as if it were the lesson: all 20 of its blocking findings asked the plan for the teaching ("the videos name
  teaching intentions but do not actually teach the concepts", "no complete question, option elimination or answer", "the
  example-first economics rule is not consistently implemented", "most remaining text is production direction rather than
  complete spoken teaching"), which the next step writes one script per video and reviews there; its checklist carried every
  lesson rule, the script rules included. The tissue plan had passed the same step with the Gemini reviewer (one minor
  finding, "v5 packs 8 concepts into a 16-minute video", a true plan finding). **Seekh → BIE (branch `task046c-plan-review`,
  `tests/test_task046c_plan_review.py`, 7 tests):** the plan reviewer gets a plan prefix (`PLAN_REVIEW_HOW`: what a plan is,
  what the scripts carry, what a plan finding is) and the plan's own checklist (`plan_checklist_text`: G-04, S2-01, S2-03), and
  `lesson.plan_review_problems` counts only structural findings as blocking (`plan_structural_finding`: a concept in no video
  or before its prerequisite, a split family, too many concepts for the minutes, a prerequisite list the chapter does not
  need; a finding that asks for the teaching, or on the wording of goal / story_or_analogy / opening_hook, is minor; an
  unplaced finding blocks). Replayed on the run's own three reviews: 20 → 0 blocking findings, so the same plan passes at
  round 0 (1 maker call + 1 checker call instead of 3 + 3); the tissue plan's v5 finding still counts as structure. Next: after
  this PR merges, the lesson job runs again (`t046c-money-lesson-b`), then the scripts' S2-08 table for Navin. The toolbox core
  lane passes (198 tests), the Task 045 lane passes (508 tests, both passed-output sets unchanged).
- **The resume (`t046c-money-understand-d`, 18:59–19:17 UTC, 18.4 minutes, ₹0; `runs/vm-t046c-money-understand-d-brain-understand/`):
  pages 4, 7, 12 and 15 passed (page 7 first try, 4 and 15 in two rounds, 12 in three), the chapter map passed at round 0 with
  0 checker findings (the baseline map had failed after 3 rounds). **Section 1 of the Money chapter is complete under Navin's
  rule: 20 of 20 pages, the map, 95 of 95 economics concept items with a checked real-world example** (MAP.md, section
  "Real-world examples (S1-16)": 37 concepts, 95 rows, every check ok). The page filter of PR #88 downgraded no finding on
  these four pages (their checker findings were not of the example-asking kind) and the slip rule was not needed.
- **The second lesson run (`t046c-money-lesson-b`, 19:57–20:45 UTC, 48.2 minutes, Codex maker and Codex checker, ₹0; `runs/
  vm-t046c-money-lesson-b-brain-lesson/`): the plan passed at round 0 with 0 checker findings** (the first run: failed after 3
  rounds, 20 findings; the plan seekh of PR #89 live), 18 videos (v0 prerequisites, v1–v15 topics, v16–v17 practice), **878
  beats, 163 spoken minutes written; S2-08: 93 of 93 economics concept items run their example first (SCRIPT.md, section
  "Real-world examples (S2-08)"); dohraav 4 of 685 beats (0.6 %), 52 % of beats open a term, a why or an example; but only
  1 of 18 scripts passed (v17)**, 17 failed after 3–5 rounds (the converging extra rounds were used by 7 scripts). Why: round 0
  had 13–52 code problems per script (book-word beats 107, the time rule 20, heavy beats 11), shrinking each round; **11
  scripts ended with 1–7 problems left, 24 of them the S2-04 everyday-Hindi check on words the list lacked** (746 flags over
  the rounds: रकम 104, वादा 30, काल्पनिक 29, स्वीकार 23, भुगतान 18, गेहूँ 13 …); 6 scripts reached code-clean and the checker found
  1–4 blocking findings each (narration pointing at BIE's own source packet: "supplied figure", "source-listed", "October 2022
  entry", "answer codes in the original continuation"; aggregates named before their numerical example; duplicate recaps; a
  reversed definition of interoperability). **Seekh → BIE (branch `task046c-money-words`, `tests/test_task046c_money_words.py`,
  7 tests):** `simple_hindi.json` 2026-10-27.2 adds 192 everyday words of money, shops, banks and payments (रकम, वादा, भुगतान,
  गेहूँ, बकाया, जेब, बटुआ, बोरी, किराया, सौदा, रसीद, पर्ची, हथेली, सुनार, तराज़ू, चायवाला, दूधवाला, साबुन, जूते, साइकिल, मुफ्त …; the
  formal ones, काल्पनिक, निर्देश, मान्यता, मुख्यतः, महत्त्वपूर्ण, दायित्व, stay hard: the English word in brackets is the way);
  `visual_grammar.json` 2026-10-27.1 extends W-01 with 13 English patterns for narration that points at the source packet
  ("supplied figure", "source-listed", "source text", "answer codes", "original continuation" …), so code catches what the
  checker found on 5 scripts. Replayed on the failed scripts' last answers: the words alone make v1 code-clean, 7 scripts keep
  1–3 problems (formal words, a book-word beat, a clipped note) and 9 wait on the checker, so the lever is the lesson resume
  (`t046c-money-lesson-c`: every failed script continues from its last answer with fresh rounds, round 0 without a maker
  call). Next: that resume after this PR merges, then the chosen video and PR 3. The toolbox core lane passes (205 tests), the
  Task 045 lane passes (515 tests, both passed-output sets unchanged under the extended W-01).

- **The lesson resume (`t046c-money-lesson-c`, 23:53–00:16 UTC on 28 October, 22.8 minutes, Codex maker and Codex checker,
  ₹0, 91 calls; `runs/vm-t046c-money-lesson-c-brain-lesson/`): 7 of 18 scripts pass** (v0 prerequisites, v1, v3, v6, v7, v15,
  v16; before the words seekh 1 of 18), 11 fail after 4–5 rounds; S2-08 still 93 of 93 examples run first; 886 beats, 168
  spoken minutes; dohraav 7 of 695 beats (1.0 %). Every script continued from its last answer (round 0 without a maker call);
  the words seekh held: S2-04 flags over the run 36 (before 746), all formal words (सफर, काल्पनिक, सुलभ, देय, मान्य, मुख्यतः,
  व्यापक, सहमति, देनदारी, दर्ज); book-word beats 27 (S2-07), the time rule 6 (S2-01). **v17, passed in the second run, failed
  here:** the new W-01 pattern `answer codes?` caught its exam instruction "फिर answer code चुनिए" (a false positive of PR #90:
  the exam's own term, not the source packet), so it continued, and the checker then failed three patch rounds on its notes
  ("the notes document only a b12 wording correction"). What the checker still blocks on across the 11: **the maker's notes**
  describing the repair instead of the unit (v2, v5, v17; v5 and v17 fail on nothing else), a code fault: a resume starts a
  script with `notes: None` (`_script_value`; `lesson_plan.json` never stored the notes), so the first patch's notes become the
  script's and `merge_notes` keeps that `about` for ever; **the time ceiling** (v2 11.1 against 11.0, v11 10.5 against 10.4,
  v14 8.9 against 8.8: the code's S2-01 check passed each, the checker reads the measured minutes in the review message and
  blocks on the 0.1); duplicate recaps (v9, v11); the code's S2-07 and S2-04 on v4, v8, v10. **Seekh → BIE next, in its own PR
  (`task046c-lesson-notes`):** the resume carries the notes and a finding only on the notes is minor (the notes are for the
  checker, never what the learner hears); a time finding is minor when the code's time check passed (code measures time);
  W-01 `answer codes?` narrowed to the source-pointing forms; सफर joins the everyday list (SEEKH_LOG entry 22). **Done on branch
  `task046c-lesson-notes` (`tests/test_task046c_lesson_notes.py`, 9 tests): `lesson_plan.json` keeps each script's notes and a
  resume starts from them; `lesson.script_review_problems` reads a notes-only finding and a time re-measure as minor (the
  review prompt says so, `lesson-script-review/5`); W-01 2026-10-28.1 and simple_hindi 2026-10-28.1. Replayed on the resume's
  records: 2 of the 11 failed scripts (v5, v17) have 0 blocking findings on their last review, 9 of 32 blocking findings read as
  minor (7 notes, 2 time), run b's v17 has 0 W-01 hits (before 1, the false positive), nothing real lost over the 18 last
  answers. Next: the resume `t046c-money-lesson-d` after the merge.** **The resume `t046c-money-lesson-d` (02:47–03:03 UTC on 28 October, 15.6 minutes, Codex maker and Codex checker, ₹0, 47 calls, 28.8 minutes of call time; `runs/vm-t046c-money-lesson-d-brain-lesson/`): 13 of 18 scripts pass** (7 before; the 11 continued scripts: v5, v8, v9, v13, v14, v17 passed, v5, v13 and v17 at round 1), dohraav 0 of 697, S2-08 93 of 93, 886 beats, 165.9 spoken minutes. The seekh held: no script failed on its notes or on a re-measured time. The 5 that still fail after 4–5 rounds fail on the checker's content findings, each a real one: v2 and v4 narrate what the source lacks ("dates नहीं हैं", a caption that audits the source; W-01), v10 adds outside banking facts without a dated basis, v11 and v12 name the route (UPI, BBPS) before the example runs (Navin's example-first rule, read on the whole part, not only on the term beat the code checks). Next seekh candidates, not built now: the code's S2-08 check reads the term's first mention anywhere in the part, not only the naming beat; W-01 adds the "what the source does not give" forms. **The proof
  before the real run is complete (ROADMAP 046 Part C, addition, point 4):** per concept the example BIE chose with its check:
  Section 1, 95 of 95 items (48 definitions, 33 cause–effect, 14 processes), all `ok`, MAP.md "Real-world examples (S1-16)" in
  `runs/vm-t046c-money-understand-d-brain-understand/`; pages first try 3 of 20 (pages 1, 7, 20; the rest 2–3 rounds, 4 pages
  needed the resume); Section 2, 93 of 93 items run their example before the term, SCRIPT.md "Real-world examples (S2-08)" in
  the resume's folder; scripts first try 0 of 18 (every script needed patch rounds), passed 7 of 18. **The chosen video: v1
  "Money क्या है, और हमारे कौन-से काम करता है?"** (topic video, 32 beats, 7.9 spoken minutes against 6.0–8.0, passed after 2
  rounds; 11 story pieces: kirana shop, market stalls, neighbourhood market, tea stall, electronics shop, grocery shop, a bank
  account, a bank home-loan account), the first topic video of the course and Navin's own kind of example (dukandar, bazar,
  log). Its places against today's kits: 8 pieces → the shop kit (C); the tea stall has no place word yet; the two bank pieces
  have no kit (B, "world kit for a bank" in the missing-capability log). PR 3 builds the bank kit and teaches the shop kit the
  tea stall and the English "bazaar"; then the canvas plans on the VM, the render in CI, the review copy and page, STOP.

### PR 3 · the bank kit, and the tea stall and the bazaar as shops (28 October 2026)

For the chosen video v1 ("Money क्या है, और हमारे कौन-से काम करता है?"): its two bank story pieces (a worker saves ₹500 in an
account, store of value; a borrower's ₹10,000 EMI falls due and is paid, standard of deferred payment) had no world kit, and
its tea-stall piece no place word. IMPLEMENTED by tests and by the preview renderer on the kit's own fixture (five stills
read: the front fits the frame at zoom 1, the teller stands behind the counter, the customer before it, the board flips
₹0 → ₹500 → ₹0 with the old value struck out, coins fall on "जमा" and "निकालता"); INTEGRATED only when v1's plans flow through
it into the rendered video; nothing ACCEPTED before Navin's verdict; ₹0.

- `bie/brain/video/world.py`: `KITS["bank"]` ("a bank with its customers at the counter"), the bank's words (खाता, खाते,
  passbook, पासबुक, savings, बचत, instalment, किश्त, teller, cashier; never the English "account" alone, since money's "unit of
  account" is a shop story), the tea stall, the market stall and the English "bazaar" as shop words; new element kinds `bank`,
  `teller`, `board`; `PLACE_KINDS` (the element that is a kit's place) and `compile_world(..., kit=)` (or `plan["kit"]`): a bank
  story drawn as a shop is refused with "a world in bank needs its place: add a bank element", a plan without any place with
  "add a shop or a bank element"; the report carries `kit`.
- `bie/brain/video/blocks/toolbox/world.tsx`: `Bank` (a stone front with a pediment, pillars, a sign band, a teller window and
  a counter; the teller is drawn before the counter so the counter hides the legs) and `Board` (a standing display whose value
  changes on its cue word, the old value struck out, a green up or a red down arrow) in the street layer; procedural people as
  before, no third-party art.
- `bie/brain/canvas_director.py`: `world_from(stub, value, kit=)` writes the kit into the plan; `check_plan` takes the mode
  dict (the kit) or the letter; the world role names the kit's place element; `WORLD_SCHEMA` lists the new kinds from
  `world.KINDS`. `world_director_card.md`: the `bank`, `teller` and `board` rows. `fake.py`: the offline maker answers a bank
  world when the beats are set in a bank.
- Proof clip `econ-world-bank-saving` (batch 3, the kit fixture `tests/fixtures/task046c/store_of_value_world.world.json`,
  28 s, 14 elements, 6 camera moves, a change every 2.0 s, longest still 3.2 s) in the toolbox demos and the registry.
- Tests: `tests/test_task046_canvas.py` (the bank fixture compiles as C with the bank kit; a bank story is refused until it has
  its bank; tea stall, bazaar and bank words find their kit; a factory still has none), `tests/test_task046_canvas_director.py`
  (a bank story goes to C with no missing-kit line, a factory story falls back to the canvas and logs "world kit for a
  factory", a bank plan drawn as a shop is refused with the kit named); the econ proof clips are now 6. The toolbox core lane
  passes on this branch.
- v1's story pieces under this kit: kirana shop, market stalls, neighbourhood market, electronics shop, grocery shop, simplified
  local market and now the tea stall → the shop kit; bank account and bank home-loan account → the bank kit; 11 of 11 pieces
  have a kit, so v1 renders every story part as an L3 world (C) and no missing-capability line. Next: the canvas plans by BIE on
  the VM (`--section canvas`), the render in CI, the review copy and page, STOP.

- **Seekh from the first real plans (branch `task046c-board-fit`, SEEKH_LOG entry 23):** the v1 canvas job `t046c-money-canvas-v1b`
  (8 of 8 parts, 6 first try, B 2 / C 6, 421.5 s, 12 Codex calls, 5.1 minutes, ₹0; the first job `t046c-money-canvas-v1` stopped
  at preflight on the VM's default Google reviewer route, gemini-3.1-pro not found, though the canvas section has no reviewer
  round) wrote sentences into the world's boards (63 of 98 values over 16 characters) and the text ran out of its box in 5 of 9
  stills. Now code wraps a board's value at spaces (the maker's line breaks kept), refuses more than 3 lines of 26 characters,
  a price tag over 9 characters and a title over 30, and the block fits the font and the box to the lines; all 63 long values
  fit after wrapping, 5 of 6 world plans compile (one price tag "₹100 / basket" is refused: "use a board for words"). The
  render of the first plans (workflow run 40619059768, dest `t046c-money-v1`) is the before; the canvas job runs again after
  this merges, then the render again.

- **Seekh from the first render (branch `task046c-camera-fit`, PR #96, SEEKH_LOG entry 24):** the first render opened scene `v1_s3b`
  on a dark band across the top: the core `Scene` camera scales a key's box by `min(1/w, 1/h)`, so a box that is not square in
  frame fractions shows the backdrop. `canvas.fit_box` now grows every camera box to the square of its longer side, centred and
  kept inside the frame; 1 of 9 keys of the first spec was not square, 0 of 8 in the second (`tests/test_task046_canvas.py`).

### PR 4 · render speed (27 October 2026)

Built on branch `task046c-render` (IMPLEMENTED; measured on this machine, 4 CPUs, the same 60 frames before and after;
the CI pipeline's own proof runs on the kit's two fixtures when the workflow's PR opens; cost ₹0):

- **Where a frame's time went** (profiled, `page.screenshot` against CDP `Page.captureScreenshot`, with and without
  Chromium flags): on a plain paper canvas the React update and layout took about 35 ms, Chromium's own capture 110 ms,
  but Playwright's `page.screenshot` 480 ms, and compositing the page through the emulated GPU (SwiftShader) another
  250 ms a frame. Two changes in `preview/stills.mjs`: frames are captured straight from the compositor once `setFrame`
  has painted them (`--capture playwright` keeps the old path), and the page is composited in software
  (`--disable-gpu-compositing`; WebGL still runs on SwiftShader in the GPU process: the three.js and matter.js proof
  clips draw as before). The frames are the same pixels (max difference 1 of 255 on two world frames, 0 elsewhere).
- **The blocks:** no per-frame SVG blur or `drop-shadow` filters (depth by colour and opacity; the icon shadows were
  already drawn as ground ellipses), the world's static layers (sun, far and near skylines, road, foreground bushes) are
  memoised and composited as cached layers moved by CSS transforms, the vignettes are static radial gradients, the
  canvas's camera layer is composited (`will-change`). The look held (side-by-side stills).
- **Measured, seconds per frame (1920 × 1080, 30 fps):**

  | Scene | before | blocks only | blocks + capture + compositing | gain |
  | --- | --- | --- | --- | --- |
  | plain canvas + curve (Phillips) | 0.618 | 0.634 | **0.256** | 2.4× |
  | canvas with L3 touches (demand-pull) | 0.859 | 0.799 | **0.303** | 2.8× |
  | world (demand-pull street) | 1.606 | 0.862 | **0.373** | 4.3× |

  A 6-minute video (10,800 frames) at about 0.3 s a frame is 54 machine minutes; in 8 chunks on GitHub's runners that is
  about 7 minutes of rendering per runner plus about 5 minutes of setup, well inside the 60-minute wall-clock target
  (before: 2.5–4.8 hours of machine time).
- **Chunks in CI:** `render.mp4_range` (frames [first, last) of a spec, `stills.mjs --from --to`, from PR #75),
  `tools/render_spec.py` (`chunk` on one runner, `join` → `video.mp4` and `review-720p.mp4`, `measure` → `cost.json`
  with seconds per frame, wall-clock, machine minutes and ₹ at the list price, `bench` for before/after on the same
  frames, `fixture` = the kit's canvas + world + credits as one ~70 s spec, `summary`), and the workflow
  `.github/workflows/task046c-render.yml` (`prepare` reads a run folder on `blindtest-results` or makes the fixture spec;
  `render` matrix of N chunks, 16 in parallel at most; `finish` joins, measures, uploads `t046c-video` with the full MP4,
  and publishes only the review copy and the report to `blindtest-results`). Runs by hand and once on the PR that
  changes it. F-13d's cache path is used here from the start.
- **Proven on this machine end to end:** `fixture` (the kit's canvas, world and credits: 2,186 frames, 72.9 s) → two chunks
  (0.234 and 0.216 s a frame) → `join` (`video.mp4`, `review-720p.mp4`) → `measure` → `summary`; the CI run on the kit
  fixtures is the next proof, on the PR that adds the workflow.
- Tests: `tests/test_task046_render_speed.py` (8) in the toolbox core lane.

### The real video · v1 of the Money chapter (28 October 2026)

**What Navin sees:** the ≤ 720p review copy `blindtest-results:runs/t046c-money-v1c/review-720p.mp4` (14.9 MB, 6.94
minutes, silent with captions) and the review page https://claude.ai/artifact/UVqeuVEtVKW3dmMfUKJqKS (one still per scene, every part's mode, level, place, rounds and
spoken lines, the render cost); the full 1920 × 1080 MP4 is the artifact of run 40630915969. Status: INTEGRATED (the script from
the lesson section, the plans from the director, the kit, the CI render: one chain on the real chapter, no hand-written piece);
nothing ACCEPTED before his verdict.

**How it was made (every step BIE's, ₹0):**
- Script: v1 from the lesson resume (32 beats, 7.9 spoken minutes, passed after 2 rounds; 11 story pieces, every one with a kit).
- Plans: VM job `t046c-money-canvas-v1c` (04:04–04:10 UTC, 6.1 minutes; `runs/vm-t046c-money-canvas-v1c-brain-canvas/`,
  CANVAS.md, plans/, video_specs/v1.json): 8 of 8 parts passed, 6 on the first try, 11 rounds, modes B 2 (`v1_s1b`, `v1_s3b`:
  build-up canvas, L2 + touches) and C 6 (`v1_s1a`, `v1_s1s`, `v1_s2`, `v1_s3s`, `v1_s4s`, `v1_s4b`: L3 worlds, four in the shop,
  two in the bank), 3 of 3 story parts in a world, 416.5 s planned, 13 Codex calls in 9.8 minutes on the ChatGPT plan; the first
  job on the same input (`v1b`, 02:23 UTC) had 6 first try and 10 rounds and is the before of entries 23 and 24.
- Render: `BIE Task046c Render` run 40630915969 on main `4de445b0` (6.94 minutes of video, 12,496 frames at 1920 × 1080
  30 fps, 8 chunks in parallel, 3.6 minutes wall-clock, 25.5 machine minutes, 0.122 s a frame, 3.67
  render seconds per video second, ₹17.1 at the list price, billed ₹0; the first render of `v1b`'s plans: 7.03 minutes,
  3.7 minutes wall-clock, 26.6 machine minutes, 0.126 s a frame, ₹17.84).
- Page: `tools/task046c_page.py` (PR #97) on the two folders and the review copy; the stills are the review copy's own frames.

**Measured on the second plans against the first:** board values 152 (87 over 16 characters), 0 over 3 lines of 26 after
wrapping (before: 123 values, 71 long, 2 price tags over 9: "₹100 / basket", "₹200 / basket"; now "₹100", "₹200"); camera keys
with a box not square 0 of 8 (before 1 of 9); scenes opening on a dark band 0 of 9 (before 1 of 9).

**Navin's to decide:** the verdict on v1 (direction, what to fix first, any part in the wrong mode); locking examples in
`explanations.json`; the next video.

## Navin's verdict on Money v1 and the work after it (29 October 2026)

**His words (also in ROADMAP 046):** "achha laga ki us concept ko real world example se samjhaya gaya ... thoda kaam hume explain
krne ke jo text lines screen par dikh rahi hai us par karna padega yaani teacher ki naration uske sentence aise poore ho ki
banawati na lage aur cheejen samjhane ki process us par depend hai to unka complete tarike se istemal hona jaruri hai ... baaki
kaam ki disha theek hai, is type ke outputs se economy samjh aa jaayegi bacho ko." He also asked to see, for every video, which
lines of the book it taught. The direction (B default, C for story parts, the real-world rule) is confirmed; nothing is
ACCEPTED yet. Evidence checked on v1's own outputs (`runs/vm-t046c-money-canvas-v1c-brain-canvas/plans/`,
`runs/vm-t046c-money-lesson-d-brain-lesson/`): 52 of 160 on-screen texts carry symbol codes ("Exchange ✓ · Account ✓ / Store ·
Deferred", "Money = balance / Device ≠ money", "EMI amount agreed ≠"), the narration reports states ("cash ₹500 से ₹400 हुआ",
"savings ₹0 से ₹500 हुईं": 29 of 886 Money beats, 4 of v1's 32), nothing checked that a text was complete or spoken.

### Work A · screen text and narration (branch `task046c-screen-text`; SEEKH_LOG entry 25)

- **Rules.** `canvas_profile.json` 2026-10-29.1: CV-13 (a complete phrase in the learner's language, one idea per board or
  box, never a code: no ✓ ✗ ≠, no list of bare words, no line ending on → = : /), CV-14 (every text is explained: its key
  words are said in the narration of its cue beat), CV-15 (a caveat once per part), CV-16 (numbers on screen are the
  narration's numbers). Vision rulebook 2026-10-21.15: S2-09 (complete teacher sentences; a story's numbers told as what
  happened, never a state report) and S2-08 says the same about its numbers. `teacher_examples.json` 2026-10-29.1 carries
  Navin's line as the good narration ("pehle aapke paas 500 rupaye the, kiraane ke 100 diye, ab 400 bache") beside the
  state report it replaces. Both director cards carry the text rules.
- **Code.** `bie/brain/video/screen_text.py`: the rows of a canvas or world plan (boards, steps, tags, labels, callouts,
  values, tables, trees, arrow labels) checked against the narration of their cue beat; `canvas_director.check_plan` runs it
  on every real plan in both modes (the compilers keep refusing what cannot be read; the kit's proof fixtures are not lessons
  and stay as they are). `soul.state_report_problems` in `lesson.check_script` (S2-09; a regression rule change, so earlier
  passed scripts report it as a changed rule, not a failure). A board holds 3 lines of 40 characters (a complete sentence;
  the block fits long lines at 36 px in a wider box). `tools/lock_explanations.py --what narration --lesson <run>` locks the
  spoken beats of locked examples (`narration`, `narration_locked`, `narration_version`); the script maker then gets them as
  "locked narration" lines to keep word for word. `tools/task046c_page.py --before-canvas/--before-lesson` lists every
  on-screen text and every beat that changed between two runs, by id.
- **Before, measured on v1's outputs (the after is the re-run's):** 93 of 186 on-screen texts refused by the new checks
  (CV-14 not spoken 38, CV-13 codes/unfinished 37, CV-16 numbers 17, CV-15 caveat 1); 29 of 886 Money beats are state reports
  (v1 4 of 32). Tests: `tests/test_task046c_screen_text.py` (10), the canvas, director, soul, real-world, shots, seekh,
  lesson-notes, money-words, plan-review, page-review, decisions and page suites updated.
- **Next (after this merges):** the lesson resume for v1 under S2-09 (`t046c-money-lesson-e`, Codex, ₹0), the canvas job
  (`t046c-money-canvas-v1d`), the render (`t046c-money-v1d`), the page with the before/after, then the narration lock of
  v1's 11 examples (the decision of PR #99); works B to E follow, each its own PR.

### Work B · which book lines did this video teach (branch `task046c-coverage`, on top of work A)

- **By code, no AI call, nothing by hand.** `bie/brain/coverage.py`: `video_coverage(chapter, lesson, video_id, spec, plans)`
  takes the lines the chapter map assigns to the video (`lesson.video_scope` on the plan's video, the same scope the script
  was checked against; the prerequisite video is measured against the map's prerequisites by name), the beats that cover
  each line (`covers_item_ids`), where each beat plays in the rendered video (the video spec's captions, one per beat,
  now carrying their `beat_id`; an older spec is matched to the plans' beats in order, else by text), how the beat teaches
  (its `purpose`: example se, samjhaya, galatfahmi door ki, dohraav, tulna, exam tip, process, sawaal, kahani, analogy,
  pehle yeh jaan lo, hook) and the teacher questions answered. Below the table: the assigned lines no beat covers (must be
  none), the beats whose basis is outside the book, and beats covering lines outside the video's scope.
  `chapter_coverage(chapter, lesson)`: every teachable line and the video that teaches it, with that video's status.
- **Pages.** `tools/task046c_page.py --lesson <run> --chapter-map <run or file>` adds the section "Kitaab ki kaun-si lines
  is video ne padhaayi (table B)" to every review page (page, line id and kind, the book line, beats with their mm:ss,
  how, questions answered; uncovered lines in red with a red box; outside-basis beats in a fold) and writes the record
  as `<page>.coverage.json` (schema `bie.brain.coverage/1`, the review record work D locks).
  `tools/task046c_chapter_page.py --chapter-map --lesson --html [--page v1=URL]`: the chapter page (teachable lines, lines a
  passed video teaches, lines in failed videos, lines no video is assigned to in red; one row per video; one row per line
  with its video, status and whether a beat covers it; `<page>.coverage.json`, schema `bie.brain.coverage.chapter/1`).
- **Measured on the Money chapter's real runs** (`understand-d`, `lesson-d`, `canvas-v1c`): v1 teaches 13 of its 13
  assigned lines in 32 beats, all 32 timed from the captions, 47 of 47 teacher questions answered, 0 lines not covered,
  10 beats with an outside basis (the hook, the shop examples, the misconception), 0 beats beyond its scope. The chapter:
  383 teachable lines, 383 assigned to a video, 0 unassigned; 246 taught by a passed video, 137 in the five failed
  videos (v2 32, v4 31, v10 27, v11 22, v12 25); every scripted video, passed or failed, covers every line it was given.
- **Tests:** `tests/test_task046c_coverage.py` (11: scope from the map's concepts, beats with times and how, questions,
  uncovered and beyond-scope lists, the prerequisite video, the card_parts fallback, caption beat ids, the older-spec
  match, the chapter record and its unassigned list, both page tools with the red case). Status: IMPLEMENTED by tests and
  by the run on v1's real outputs; INTEGRATED when the next render's page is built with it (the render workflow's page
  step takes the two inputs); ACCEPTED is Navin's. ₹0.

## Navin's decisions of 29 October 2026 (recorded in his words in ROADMAP 046; built on branch `task046c-navin-decisions`)

Status words: IMPLEMENTED by tests (`tests/test_task046c_navin_decisions.py`, 11 tests; the licence, toolbox, soul,
real-world and image-job suites pass with the changed expectations); the library-first read is INTEGRATED only when the next
real understand run on a chapter with locked terms counts its hits; nothing ACCEPTED is changed. Cost ₹0 (no AI call).
**Not received: works A and B of the same brief** (the decisions say "do these after work A and B"); everything that does
not depend on them is built, and the one thing that does, the narration wording of the locked examples, is left unlocked.

1. **Lock v1's examples** ("V1 ke sabhi examples lock ho ..."). `tools/lock_explanations.py --what examples` locked the
   real-world examples of 11 of v1's 13 items (p001-i3, i7, i8, i9, i10, i11, i12, i14, i15, i16, i17: medium of exchange,
   acceptability, durability, portability, divisibility, uniformity, limited supply, barter, unit of account, store of value,
   deferred payment; the two `facts_numbers` items i4 and i5 take no example by S1-16) from
   `runs/vm-t046c-money-understand-d-brain-understand/` into `explanations.json` 2026-10-24.2: place, actors, goods,
   numbers, steps, the term after the story, `from_run` `<run>:<item>`, `locked_version`; `narration` null and
   `narration_locked` false (work A first; the version is recorded so the wording lock can name it). **Library first:** the
   page step shows the locked examples found in the page text to the maker as given, and after the answer code fills
   `unpack.real_world_example` of every item whose own unpack terms name a locked example (`example_source`
   `library:<key>`; the maker's version replaced; an item that only mentions the term keeps its own), the rest marked `ai`;
   `MAP.md` carries a Source column and the line "N from BIE's locked library (no AI asked), M from the AI"; `SUMMARY.json`
   → `quality.real_world_from_library` / `real_world_from_ai`. Replayed on the Money map (`explanations.apply_examples`):
   page 1, 11 of 11 items from the library and all 11 pass S1-16; the whole chapter, 18 of 96 items from the library (the 11
   plus 7 later items that open the same concept again), 77 from the AI, no other item touched. `docs/bie/CONTRACTS.md`
   lists every record a run writes and how a locked item points back to its run.
2. **PRs #75 (Part B) and #76 (one-shot test)** closed on 29 October 2026 with a closing comment naming what replaced them
   (Part C's kit, PRs #82–#97, the first real video; Route 2 chosen); the branches `task046-director-b` and
   `task046-oneshot` stay as evidence.
3. **Route 2 for science hero shots.** `licence_policy.json` → `generated_images`: an asset with source `bie_chatgpt_plan`
   (or the one-shot branch's `openai-image-gen`) is allowed in lessons when it carries `generated_by`, `prompt` and
   `generated_on`, refused with the missing fields named otherwise; `tools/vm_image.py` writes the three on every made
   image ("generated by BIE through the ChatGPT plan", the prompt, the date).
4. **Licences** (`licence_policy.json` 2026-10-29.1, his words in each entry): `approved_by_navin` india-code (source
   acknowledged, s. 52(1)(q)), gmt-earth-relief (the citation), bodyparts3d (CC BY 4.0 with the credit): their assets pass
   the gate with the full credit and are refused with the missing field named; the three tools' lesson verdicts are
   `allowed`, and the proof clips `bio-heart-bodyparts3d`, `geo-relief` and `astro-sky` leave the internal-proof list.
   hipparcos stays `needs_navin` (yes given, ESA's commercial terms unchecked); **the Yale Bright Star Catalogue** (BSC5,
   9,110 stars, public domain) is the sky adapter's default star source: registry `yale-bsc`, `astro.load_bsc` (the
   fixed-width V/50 columns, J2000 with proper motion), `astro.sky(catalogue="bsc")` default and `"hipparcos"` for internal
   proofs, the `astro-sky` demo and the `sky_dome` block label stars by the catalogue's own ids, the setup prefetches the
   file into the asset cache. India's boundary stays `needs_navin` with `navin_condition` (the Survey of India side-by-side
   check, shown to Navin with the review). Remotion: `software.decided` (one-person company, the free licence applies);
   the toolbox page prints it as decided.

## Task 046 · One-shot quality test (26 October 2026)

After Navin rejected Part B, BIE made one shot two ways and put it next to the benchmark before any longer render. The shot
is b37.2 of v3 (4.5 s): “खास तुलना: Simple squamous में पतली exchange boundary;”, labels “simple squamous” and “boundary”.
Draft PR #76 (branch `task046-oneshot`), not merged; PR #75 stays unmerged. Status **IMPLEMENTED**; Navin's eye decides; no
full video until he says yes. Review page (private): https://claude.ai/artifact/Pb4ZpvK7xEmpSnQvCqc5JY (benchmark frames
only there, never in the repo).

- **Route 1 · Blender studio recipe (done).**
  - `bie/toolbox/blender/epithelium_studio.py` + `epithelium_studio.json`: every epithelium member from one preset file
    (simple squamous, cuboidal, columnar, stratified).
  - The look: organic wavy interlocking outlines (dense smoothed rings, no subdivision), domed tops with a nucleus bulge,
    speckled cytoplasm, Burley subsurface scattering, key and rim light, haze, glare, depth of field, a blurred capillary
    with red cells, blue particles, a slow push-in. Cycles on CPU, seeded so chunks match; anchors projected for the labels.
  - Rendered by `.github/workflows/task046-oneshot.yml` (15 runners, 32 samples, denoised): **203 s per frame** on average
    (123–254 s on 4-CPU runners), 457 render machine-minutes, 473 job minutes, longest runner 38 minutes, **₹0** (public
    repository). Samples sweep on frame 70: 16 spp 132 s, 64 spp 353 s, 128 spp 824 s per frame.
  - Labels from the anchors and the kinetic caption by BIE's code (`tools/oneshot.py route1`, the `plate` block): 127 s.
    Review copy and look frames: `blindtest-results:runs/t046-oneshot/route1/`.
- **Route 2 · AI still + BIE code (done).**
  - BIE writes the prompts (`bie/brain/video/still_prompt.py`, Route 1's camera and layout, no text in the picture):
    `runs/t046-oneshot/route2/prompts.json`.
  - Images: VM job `t046-oneshot-images-4`, Codex's built-in image_gen (gpt-image-2) through the ChatGPT plan, no API key:
    4 of 4 images (1672 × 941, 26–32 s each, job 2.05 minutes, plan usage 0 % before and after, **₹0**). Three earlier
    jobs made no image; the causes and fixes are F-14 and F-14b in `main`'s STATUS (PR #80; PR #81 after Navin's yes).
  - Checked by eye (`runs/t046-oneshot/route2/IMAGE_CHECK.json`): no text in any image, one thin layer of flat cells,
    one nucleus each, a capillary with red cells behind the far edge; none rejected; still c chosen (clearest nuclei,
    lit centre cell).
  - Moved by BIE's code (`tools/oneshot.py route2`): Depth Anything V2 Small (Apache-2.0, pinned, ONNX Runtime) depth map
    in 17 s on CPU, the `parallax_plate` block (depth displacement, push, particles, glow, labels placed from the depth
    map, caption) in 150 s. Review copy and look frames: `blindtest-results:runs/t046-oneshot/route2/`.
  - OpenAI's terms give the user the output; the licence gate records image output as `openai-image-gen`, `needs_navin`
    before any lesson uses it.
- **LOOK-01 (advice only)** — job `t046-oneshot-look-both`, free Google key (`gemini-3.8-flash` direct), against a written
  description of the benchmark (its frames never leave the private page; Navin can put three frames in
  `/var/lib/bie/private/refs/t046-benchmark/` on the VM for a frame-to-frame check):

  | | organic shape | translucency | lighting and depth | detail | science | same class | mean | verdict |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | Route 1 · Blender | 6 | 4 | 6 | 5 | 6 | 5 | 5.3 | close |
  | Route 2 · Codex still + BIE code | 7 | 7 | 7 | 7 | 7 | 7 | 7.0 | same class |

  Biggest gaps: Route 1, “the materials lack wetness and deep subsurface translucency”; Route 2, “the floating blue
  spheres appear slightly detached due to minimal contact shadowing”. Ledger estimate ₹1.10 at the list price, billed
  ₹0. (The first Route 1 check, `t046-oneshot-look-r1`, gave 5.2.) `runs/vm-t046-oneshot-look-both-brain-look/LOOK.md`.
- **Runner fixes on the way (merged):** PR #79 (F-13c, F-11 in the toolbox lane), PR #77 (VM image and look jobs), PR #80
  (F-14: a poll that moved `main` runs again with the new code; a failed image run keeps Codex's error; the imagegen skill),
  PR #81 (F-14b: image calls keep Codex's code-mode host on; Navin said yes, 26 October 2026).

## Task 046 · Part B, the blocks, the composer and the benchmark render (26 October 2026)

**Navin's verdict, 26 October 2026: rejected.** In his words: “Part B ke dono routes ki video benchmark se bilkul mel nahi khati, reject. Part C shuru mat karo. PR #75 merge mat karo jab tak Navin agla faisla na de.”
Both routes' videos (`blindtest-results:runs/t046-v3-benchmark/A/review-720p.mp4` and `C/review-720p.mp4`) do not match the epithelium benchmark. Status stays **IMPLEMENTED** (not ACCEPTED). PR #75 stays open and is not merged until his next decision; Part C is not started.

Built in Part B (IMPLEMENTED; the demo clips and the segment render are made by CI; nothing ACCEPTED until Navin's verdict):

- **18 blocks as code** (`bie/brain/video/blocks/toolbox/benchmark.tsx`, `grammar.tsx`; `equation_steps` already in `maths.tsx`).
  The world block `cell_sheet` draws one three.js scene per script part from a timeline of shots (`data.shots`: member, focus,
  flow, camera move, cutaway, exploded, stretch, dim, labels, organ), so `particle_flow`, `focus_glow`, `organ_zoom`,
  `leader_label`, `camera_path`, `cutaway` and `exploded_view` act inside one canvas and one camera (VG-01, no cuts); each is
  also registered by name with its own preset. The 2D grammar blocks (`kinetic_caption`, `board_build`, `mnemonic_card`,
  `concept_arrow`, `split_compare` with two worlds side by side, `scale_compare`, `flow_arrows`, `graph_plot`, `timeline`)
  draw HTML and SVG on the dark field, one accent per member (`accents.json`, read by the TSX and by the composer). A procedural
  Earth (shells and a bar magnet tilted 11°) is the L4 demo world for `cutaway`, `exploded_view` and `flow_arrows` (Navin,
  26 October 2026). The composition is 1920 × 1080; a smaller output (a 720p clip or review copy) is the same picture scaled as a
  whole (`Video.tsx` Stage), and the 3D canvas draws at the output's pixel size.
- **Demo clips with frame checks:** 17 clips in `bie/toolbox/demos.py` (ids `bench-*`, batch 1, group `bench` of the toolbox demos
  lane, its own job, 1280 × 720, 3.5–4.5 s each), one per block; each clip's stills are checked against the rules it serves
  (`frame_checks.demo_rules`: B-11/VG-09 dark field or a dark border in a close-up, B-08 caption band, B-10 the member's accent on
  screen, B-03 a label box lit, VG-01 motion; a rule no frame check can judge fails). Registry entry `bie-benchmark-blocks`
  (`demo_proven`, batch 1, BIE's own code, version `2026-10-26.1` of the registry), proof = the 17 clips.
- **The composer** `bie/brain/video/compose.py`: the director's plan (Part A) → VideoSpec; one world layer per scene whose shots
  carry every clause's flags, the member read from the clause and carried across clauses (two members named keep the carried
  world), focus and labels from the clause, particles by the verb (absorb, secrete, cross, sweep, shed), a kinetic caption per
  clause (the English terms in the accent, the yaani half marked), boards that fill across the scene, mnemonic cards, split
  screens by member, the family tree, reason arrows and scale bars; the world rests (dims) while a panel teaches; credits
  last. `check_spec` keeps said = shown on the finished spec (B-03, B-08, B-01); `shot_frames` gives every shot's frame range.
- **Voice:** `bie/brain/video/voice.py`, eSpeak NG as a placeholder (Hindi runs in the `hi` voice, Roman runs in `en`, one WAV per
  beat, mixed into one track at the shots' frames); its real seconds drive the timing, so every shot sits on a sound that exists
  (`compose --voice espeak`; `--voice silent` keeps the text estimate). The real voice is Task 047.
- **Route A and route C:** route A is the procedural world; route C builds every member with Blender (`bie/toolbox/blender/cell_sheet.py`:
  simple and stratified members, cilia, microvilli, dome and keratin layers, a gland duct; `render_video.py models`) and the
  same block draws the glTF per member (`data.models`), so the two routes are measured on the same spec.
- **The render tool** `tools/render_video.py`: `compose` (refuses a plan the director blocked: W-01 or another blocking check, unless
  `--allow-blocked` for a pipeline check), `models`, `chunk` (frames [i·N/k, (i+1)·N/k) through the preview renderer: Chromium +
  SwiftShader + ffmpeg, the same blocks real Remotion renders; Task 046a's bridge proof showed the same frames), `join` (the
  narration muxed, the ≤ 720p review copy), `measure` (render seconds per second of video, machine minutes, USD and ₹ at the
  GitHub list price of $0.008 per minute at ₹84; the public repository bills ₹0), `report` (one still per shot from the finished
  video → `frame_checks` → the 24-rule table with the first failing frame, RULES.md, SHOTS.md, contact sheets, report.json),
  `bridge` (the first 10 s rendered again by real Remotion 4.0.536 and compared frame by frame), `summary`; `tools/benchmark_page.py`
  makes the review page for Navin from the published folder.
- **CI:** `.github/workflows/task046-benchmark.yml` (by hand, and once when the file changes in a PR): compose from the passed
  lesson run (the shot list by code, `tools/shot_list.py`), route C models, chunks in parallel per route (8 runners each),
  bridge, join + measure + report per route, summary, publish to `blindtest-results:runs/t046-v3-benchmark/` (review copies,
  REPORT.md, RULES.md, SHOTS.md, cost.json, contact sheets, bridge). The toolbox lane now runs the `bench` demo group as its own
  job; `espeak-ng` is installed in the wrappers and demos jobs.
- **The segment:** v3's part c07.1 (the epithelium family, beats b20–b38; the five W-01 beats were all in it): 76 shots, 12
  members, main level L5a, one visual change every 4.59 s (33 camera moves added by the director); about 5.6 minutes at the
  placeholder voice's pace (5.0 at the text estimate).
- **VM job 1 (Part A's last step) done, ₹0 billed:** `docs/evidence/task046-director/W01.md` has the five sentences before and
  after; SEEKH_LOG entry 12 (the estimate of a lesson resume now scales to the scripts asked: `cost.lesson_share`).
- **Tests:** `tests/test_task046_blocks.py` (19 tests, standard library, in the toolbox core lane and the canonical gate): the 18
  blocks registered and imported, every flag the composer writes, every block with a demo clip and its rules, the L4 clips on the
  Earth world, the registry entry's claims, the composer on the real v3 segment (one world, a caption per clause, members carried,
  panels dim the world, said = shown fails on an unsaid label, voice and credits in the spec), the compose command (refuses the
  blocked fixture, composes it as a pipeline check, route C models per member), chunk ranges and the cost at the list price, the
  rule table merged with frame findings, the seekh of VM job 1, the Blender script's members and names; `tests/toolbox/test_task046_frames.py`
  (7 tests, wrappers lane: Pillow, eSpeak NG, Blender): the frame rules on synthetic stills, per-shot findings with frame numbers,
  the contact sheet, the placeholder voice's WAVs and mix, the Blender members with their hairs and layers. The two passed-output
  sets still pass.
- **CI numbers (benchmark run 40298550697, 26 October 2026, on this PR; published to `blindtest-results:runs/t046-v3-benchmark/`):**
  the segment is v3's part c07.1 from the VM run `vm-t046-v3-wording-patch-resume-brain-lesson` (the patched, passed script):
  77 shots, 337.6 s (326.1 s spoken by the placeholder voice, 4 s of credits), 10,129 frames at 1920 × 1080, 30 fps; main level
  L5a 93.6 % (73 shots, 305.1 s), L3 6.4 % (4 shots, 21.0 s); one visual change every 4.59 s (71 changes; micro band 3–5 s, met).
  **Route A** (procedural world): 9,198 render seconds on 8 runners, **27.2 render seconds per second of video**, 153.3 machine
  minutes (wall clock 25.4 min in parallel), **USD 1.23 = ₹103 at the GitHub list price, billed ₹0** (public repository); review copy
  `A/review-720p.mp4` (19.6 MB). **Route C** (Blender glTF sheets, 12 members built in 2–6 s each, 0.8–3.7 MB per member): 10,148
  render seconds, **30.1 s per s**, 169.1 machine minutes (wall 45.5 min), USD 1.35 = ₹114, billed ₹0; review copy `C/review-720p.mp4`
  (16.4 MB). Per runner about 3 minutes of setup (Node, the web packages, Chromium) come on top of these render minutes. **Bridge:**
  the first 10 s of route A rendered again by real Remotion 4.0.536 on the same runner class: 37.5 s per s with bundling (375 s)
  against 20.8 s per s on the preview path; the three stills compared are identical (mean difference 0.0 grey levels). **24-rule
  table with frame numbers (77 stills read, one per shot):** route A 14 pass, 2 partial, 2 fail, 6 n/a; route C 15 pass, 2 partial,
  1 fail, 6 n/a. Partial: B-01 (15 clauses over 6 s, 4.2 s on average), B-02 (seconds per member uneven: stratified squamous 54.8 s,
  transitional 50.6 s, pseudostratified 14.1 s). **Fail: B-10** in both routes (the member's accent is not on screen in 18 stills of
  route A and 21 of route C, first at frame 1004, shot b21.4: the glow on the lit structure is too soft to read in a far or crowded
  shot); **B-03** in route A (4 stills show no label box though the clause names things, first at frame 1682, shot b23.1: the label's
  part is not in that member's world, so the overlay drew nothing; route C passes the same check only because its paler sheet reads
  as "bright text", a weakness of the pixel check, not a difference between the routes). Seen on the contact sheets, for Part C:
  after an organ zoom the camera stays far for the next clauses (the sheet is small in the frame until the next camera move); route
  C's Blender materials are paler and its nuclei fainter than route A's; the organ shapes are crude. Nothing of this is hidden from
  the report: `REPORT.md`, `RULES.md` and `SHOTS.md` per route, `cost.json`, the contact sheets and the bridge sheet are on the
  branch; `docs/evidence/task046-benchmark/` keeps the text files; the review page is `tools/benchmark_page.py` on that folder.

Navin's verdict is given (rejected, above). Open for his next decision: what happens to Task 046 after the rejection; PR #75 waits for it.

## Task 046 · Part A, the code director (26 October 2026)

Navin's decisions, 26 October 2026, in his words (also in ROADMAP 046):

- "Task 46 will surpass even the tarazu point 'video kaisi ho' level on its full completion, implementing things required."
- "90 se 99 percent videos L3 ya isse upar ke level ki ho." Chain: content decides the scene plan; the scene plan decides which
  visual level the video code is made at; BIE itself must be capable up to L5a.
- Verdict of 25 October: present the book's knowledge with completeness, teacher style, examples and analogies, "like a truly
  class animated video" (the epithelium benchmark); video length stays open, driven by completeness.
- Narration never says "book के अनुसार", "किताब कहती है", "book says" or any wording that points at the book; BIE teaches as a
  teacher; Navin accepts the copyright position.
- Lesson assets: only CC0, public domain and CC BY (the 046a-L gate). Reference videos are for calibration only; nothing from
  them enters the public repo.

Built in Part A (IMPLEMENTED; offline and by tests; cost ₹0; nothing rendered; nothing ACCEPTED):

- **The visual level ladder:** `docs/vision/VISUAL_LEVELS.md` and `bie/brain/rulebook/visual_levels.json` (schema
  `bie.brain.visual-levels/1`, version `2026-10-26.2`; a rulebook data file, so it counts in the rulebook version). L1 teacher at
  a board (never a BIE target), L2 clean 2D, L3 rich 2D/2.5D, L4 stylized 3D, L5a photoreal micro or machine 3D (the benchmark
  level, BIE's highest), L5b photoreal humans and Pixar-grade acting (not made by code; a plan that asks for it fails the
  check). Every shot carries a level from {L2, L3, L4, L5a}. **The level rule has two stars (Navin, 26 October 2026, after the
  reference-video level cards):** A, the chapter or book target — "90 se 99 percent videos L3 ya isse upar ke level ki ho:
  kitaab se banne wali kul videos ki baat hai, aur ye koshish ka target hai, blocker nahi" — every video reports its main
  level (the level with most shot-seconds), the chapter report counts videos per main level and the share at L3+, and below
  the target it names the video and the reason; B, the shot level — "scene plan ke hisaab se kisi video ka kuch hissa L2 ka
  ho sakta hai aur usi mein koi baat L5 se dikhani ho sakti hai; poori video ek level ki bane, ye zaroori nahi" — the level
  stays per shot, the director chooses L3+ where the content allows and L2 only where it shows the point better, with the
  reason on that shot; the earlier "90 % of shot seconds or not rendered" check is withdrawn and no video is blocked for its
  level. **The pace** is the visual-change rate (a block or camera change): micro biology 3–5 s per change, engineering and
  physics 10–20 s; VG-01 checks it; where consecutive clauses would hold the picture past the band, the director adds a
  camera move (zoom on the lit structure, orbit, zoom out). Benchmark B-01 and vision rule S3-06 say 3–5 s per shot (Navin's
  approval, 26 October 2026; the benchmark measured 19 changes in 90 s).
- **The visual grammar:** `bie/brain/rulebook/visual_grammar.json` (version `2026-10-26.2`): the eleven rules of Navin's brief as
  VG-01…VG-11 (numbered VG because G-01…G-07 are the vision rulebook's general rules and an id is used once), locked, for the
  director and the visual section, so the AI director's prompt carries them too; plus **W-01** (lesson, director) with the
  word list in four groups (Hindi, Hinglish in Roman, English, mixed script: "किताब के अनुसार", "kitaab", "book … कहती है" with
  a gap, "book says", "page पर", "printed location", "NCERT", "textbook" …) and allowed examples (an everyday book in a scale
  comparison, the on-screen table). `soul.book_pointing` / `wording_problems` apply it; `lesson.check_script` sends a hit back
  as a W-01 problem; the patch hint tells the maker to rewrite only that beat; `regression.RULE_CHANGES` names the change so the
  earlier passed outputs report it as a changed rule (both sets re-checked: 0 failures).
- **Capabilities:** every entry of `bie/toolbox/capabilities.json` (version `2026-10-26.1`) carries `default_level` (validated
  against the ladder) and `blocks` (the code blocks that draw it, best first; the benchmark set and the new set of Part B:
  `leader_label`, `cutaway`, `exploded_view`, `scale_compare`, `equation_steps`, `graph_plot`, `flow_arrows`, `timeline`,
  `camera_path`); `grammar_blocks` lists the blocks a grammar rule may add to any shot. `mnemonic_card` and `split_compare`
  already had their capabilities.
- **The code director** `bie/brain/shots.py` (extends the Section 3 director, does not replace it; `to_director_video` gives
  the AI director's scene shape and passes `director.check_video`): input a passed script + the chapter items (visual verbs
  from the 045d unpack) + the level profile + the capabilities; one spoken clause → one shot with seconds from
  `video/timing.py`, capability, blocks, level, camera (establish, pan to the next part, zoom from the organ; no cuts), labels
  (the things the clause says, as phrases), caption (the spoken words with the English terms, the yaani half marked), assets
  (procedural for the benchmark blocks; otherwise the resolver's lesson-allowed sources, the licence gate unchanged). Scenes:
  one per script part (VG-01, one world). Checks: blocking = a level outside the ladder (L1, L5b), W-01, said ≠ shown
  (B-03), a clause without its shot (B-01), an unknown block; advisory = the pace against its band (VG-01), an L2 shot
  without its reason, B-02, B-04, B-05, B-06, B-07, B-09. Output `shots/<video>.json` (level mix, main level, pace),
  `SHOTS.md` with the chapter report (star A), the 24-rule table (pass / partial / fail / n/a per rule).
  `tools/shot_list.py --from-run <run> --videos v3 --out <dir>` runs it on a run folder or URL.
- **Lesson:** `run_lesson(..., only=[...])` (`run_brain --section lesson --resume-from … --videos v3`): the selected scripts
  continue from their last answers, every other script is kept exactly as it was (`kept: true`, its status unchanged).
- **Offline proof on v3** (`docs/evidence/task046-director/`; fixture `tests/fixtures/task046/v3_tissue.json`): 161 shots /
  53 beats, 624 s, 6 scenes, 0 cuts; main level L5a (86.8 % of the seconds, L3 13.2 %), chapter report 1 of 1 at L3+; pace one
  visual change every 4.14 s (7.52 s before the director added 68 camera moves; micro target 3–5 s); 24-rule table 14 pass,
  4 partial (B-01, B-02, B-11, VG-09), 5 n/a, W-01 fail; five W-01 beats listed with their sentences in `W01.md`; v3 is blocked from rendering until
  they are rewritten (W-01 is the only blocker; the level never blocks).
- **Tests:** `tests/test_task046_shots.py` (34 tests, in the toolbox core lane): the ladder and the grammar files, W-01 in its
  four forms and its allowed cases, the rule-change record, the only-these-videos resume, the capability fields and their
  validation, sentences and labels, the director on a tiny script and on the real v3 (one shot per clause, the world, the
  level split, the benchmark shots, said = shown, the AI director's checks accept it, the recorded proof matches the code),
  the checks failing what Navin ruled out (L5b, L1, an unsaid label, a missing shot, a book-pointing beat), a mostly-L2 video
  reported in the chapter report and not blocked, an L2 shot without its reason, the pace pass.
- **Part B note (Navin, 26 October 2026):** the demo clips of the L4 blocks `cutaway`, `exploded_view` and `flow_arrows` are
  made on a procedural Earth wedge and bar magnet (code only, no outside asset), since v3's micro world barely uses them.

Reference-video level cards (Navin's doc of 26 October 2026, calibration only, nothing copied): the ladder, the 11 grammar
rules and the 10 new blocks agree with this PR; its findings changed the level rule from a per-video blocker to the two stars
above and added the visual-change pace; the doc's L5a ("sabse mehnat: models, shaders, render time") is measured in Part B.

Navin's to decide after Part B: the render machine and GPU budget, block approvals, anything a source's licence leaves open.

## Task 046a-L · licence gate (25 October 2026)

Navin's decision, 25 October 2026, in his words: "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi."

Built (IMPLEMENTED; checked offline and in CI; not used on a real book yet, nothing ACCEPTED):

- **One policy, one place:** `bie/toolbox/licence_policy.json` (schema `bie.toolbox.licence-policy/1`, version
  `2026-10-25.1`, dated, Navin's words recorded) is the only source of truth; `bie/toolbox/licence.py` (standard library)
  reads it for every licence decision: `bie.brain.assets` (`licence_allowed`, `normalise_licence`, the Commons and Openverse
  search, `add_candidate`, `credits`), the toolbox sources, the registry checks (`_licence_needs` and the new
  `registry_problems`: a content tool with its own terms must be named in the policy, a per-item one must be in its per-item
  list), the resolver and the toolbox page. No per-tool verdict is written by hand.
- **Lesson content** (anything seen or heard in a lesson video, game or notes): allowed = CC0, public domain (the Public
  Domain Mark, US government works stated as public domain), CC BY of any version with author, licence, licence URL and
  source page (a missing field fails); refused = CC BY-SA and every share-alike licence (GFDL, ODbL, GPL-family on content),
  any NC, any ND, a missing or unreadable licence; needs Navin = own terms, blocked until he approves the source by name in
  the file (`approved_by_navin`, empty today); per item = NASA, Commons, Openverse, NIH 3D, PubChem, Sketchfab-type sources,
  checked file by file (a NASA file whose record names a third-party copyright holder is refused). NASA pictures are now
  recorded as "Public domain (NASA, US government work; ...)". BIE's own drawings and models (source `bie`, `bie_toolbox`)
  are allowed with no credit; the font (Noto Sans Devanagari, OFL) is software, the text set in it is BIE's.
- **Blocked for lessons today:** Z-Anatomy (CC BY-SA 4.0: refused); India Code (government terms, s. 52(1)(q)), Hipparcos
  (scientific use with citation; ESA's rules for commercial use), BodyParts3D (CC BY 4.0 page, but the project asks users to
  contact DBCLS), SRTM15+ relief via GMT (free with citation): needs Navin; any map or asset that draws India's political
  boundary (Natural Earth's India view; the `india_map` block): needs Navin until he approves a boundary matched to the
  Survey of India map. A land or coastline outline (the quake map's world-atlas land) is not a boundary.
- **Software is not content:** a program's licence (MIT, BSD, Apache, LGPL, GPL, EPL, NOSA, Remotion's own) governs the
  program, not what BIE draws with it. GPL-family programs (Blender, PsychoPy, pyGPlates, Lcapy, CadQuery's OpenCascade,
  FEniCSx, GMT, ObsPy, JSBSim) run only in the cloud, CI or VM render path; `apps_copyleft_problems` scans every dependency
  manifest and every import under `apps/` (android, web, operator, api) and a test fails if one appears. Today: none.
  Data or models a tool ships with are content (Z-Anatomy files, the Hipparcos catalogue).
- **The gate, fail closed** (`lesson_licence_check(assets)` → problems; `require_lesson_assets` / `AssetLibrary.require_lesson`
  raise `LicenceError`): the visual section checks a video's assets before its layout is paid for and again with the spec
  (`lesson_spec_check`: a block that draws India's boundary) before `video_specs/<video>.json` is written; a stopped video
  gets `status: stopped_by_licence` and its reasons in `visual.json` and VISUAL.md, and nothing is swapped. The game
  builder checks every board picture before GAME.html (a picture without an asset-library record cannot pass). The old
  path: Scene IR `resolve_assets` and the compiler's `bundle_assets` (the COMP path; `bie/video_compiler/` is an empty
  namespace) block a refused asset, and their records now carry a licence record (`licence`); a rights word the policy
  cannot read ("licensed") is refused. Every passing output gets a credits list built from the asset fields
  (`visual.json` per video, the Scene IR and bundle receipts, the game's `credits`). `AssetLibrary.require_lesson` is the
  hook the Task 046 director calls. The `allow_share_alike` switch is removed (`licence_allowed`, `search_commons`,
  `search_openverse`, `add_candidate`); named Commons and Openverse files are fetched only when a lesson may use them;
  NC and ND files are never fetched.
- **Resolver:** an asset source a lesson may not use is listed under `not_for_lessons`; when it was the only one
  (`terrain_or_layers`: SRTM15+; `flowchart` and `tree_hierarchy`: India Code as their data source) the resolution says
  "BIE draws it itself (its own model or drawing) or finds an allowed source" and the gap goes into the missing log as
  "missing lesson-allowed source" for seekh → BIE. Natural Earth sources carry the India-boundary note.
- **Proof clips are internal proofs, not lessons.** Marked "internal proof, not for lessons" (evidence kept, nothing
  deleted or re-rendered): `bio-heart-zanatomy`, `psy-brain-lobes` (Z-Anatomy, refused), `bio-heart-bodyparts3d`
  (BodyParts3D), `astro-sky` (Hipparcos), `geo-relief` (SRTM15+), `law-procedure-flow`, `law-courts-tree` (India Code),
  `geo-india-state`, `hist-gt-road` (India's boundary). The other 42 use content lessons may use. The demo runner now
  writes each clip's lesson use, blocks and the assets' credit fields into its receipt.
- **Toolbox page** (`docs/toolbox/TOOLBOX.md`): a "Lesson use" column for every tool and source and for every clip, the
  capability tables list only lesson-allowed asset sources (the others named "not for lessons"), and the old "Licences to
  decide (Navin) · Recorded, not blocked" part is replaced by "Lesson licence gate".
- **Tests:** new `tests/test_task046a_licence.py` (27 tests, standard library, in the toolbox core lane): each licence class
  (CC0, PD, PDM, CC BY 2.0–4.0, CC BY-SA, NC, ND, missing, custom, NASA with and without third-party rights), a source Navin approves by name, the policy's
  own checks, registry and page, software in apps/, and end to end: a lesson scene with a Z-Anatomy model is stopped (asset
  library, Scene IR, compiler bundle: nothing copied); a CC BY-SA Commons image is refused (never downloaded); a CC BY
  Commons image passes and appears in the credits; a CC BY asset without author fails; an India boundary map is stopped; a
  GPL tool in an apps/ manifest or import fails; the resolver's gap; a game picture without a record. In
  `tests/test_task039_brain.py`: the visual section stops a video that would show a Z-Anatomy model (no layout, no spec).
  Tests changed because the rule changed (listed, not hidden): the share-alike switch tests now check it is gone; the
  Commons/Openverse source test now expects CC BY-SA refused, not kept; the NASA test expects "Public domain"; the offline
  visual test's fake Commons reply now carries the licence URL a real Commons reply has; old-path fixtures in
  `tests/scene_ir/test_h3_asset.py`, `test_h3_integration.py`, `tests/compiler/test_comp_asset_001.py`,
  `test_comp_asset_003.py`, `test_comp_asset_integration.py` and `test_comp_h11_001.py` give their synthetic images a
  licence record (BIE's own drawing), because "licensed", "rights" and "user_supplied" are not licences the policy can read.
- **Before-images kept:** the compiler's lineage checks (`tests/compiler/test_comp_h1`–`h5_integration.py`) require that a
  file recorded by an earlier batch (`lineage/batch_009`, `hardening_h1`–`h4`) keeps its original bytes in that batch's
  lineage folder once it changes. This PR changes 8 such files (`bie/compiler/asset_bundler.py`,
  `bie/compiler/compiler_asset_common.py`, `bie/scene_ir/asset_contract.py` and five test files), so their bytes from
  `main` (`c3173571`; each matches the batch's recorded hash) are added under `lineage/<batch>/` (40 copies, nothing
  existing changed). Found by the PR's first `native-extra` run.
- **One pin converted (Task 037C rule, first edit of `bie/scene_ir/` since adoption):**
  `tests/productization/visual/test_visual_producer.py::test_native_visual_director_animation_sceneir_and_android_trees_preserved`
  pinned a hash of five whole trees (`apps/android`, `bie/visual_intelligence`, `bie/director`,
  `bie/animation_intelligence`, `bie/scene_ir`). The adopted file lists are now in
  `tests/productization/visual/preserved_trees.json` (taken from `main` `c3173571`; each list reproduces the pinned count
  and identity exactly, and the test still checks that); an adopted file that disappears still fails, a working-source
  file that changed is accepted as evolved (`scripts/source_evolution.py`). Test count unchanged (the Task 035 affected
  inventory stays 4,972). Found by the PR's `task035-affected` run.
- **Earlier passed outputs:** both sets in `tests/fixtures/passed_outputs/` (tissue understanding and lesson) re-checked with
  `tools/passed_outputs.py check`: 0 problems. They are text only (pages, map, scripts); no earlier passed output used
  refused content, so none is listed as broken.
- **Still Navin's:** India Code, Hipparcos/ESA, BodyParts3D (after DBCLS answers), citation-only data (SRTM15+ and the like),
  India's boundary (approve one matched to the Survey of India map), and the Remotion licence (free for individuals and
  companies of up to 3 people, a paid company licence above that).

## Task 046a · auzaar-ghar, batch 3: geography, history and polity, economics, law, psychology and education, languages (25 October 2026)

Built in batch 3 (IMPLEMENTED; tools demo proven; nothing INTEGRATED into a lesson run yet, nothing ACCEPTED):

- **Registry:** 21 more entries (80 in all). Maps: Natural Earth 5.1.2 at 1:10m (public domain; India drawn with Natural
  Earth's own India point-of-view boundary, so all of Jammu and Kashmir and Ladakh are India's) and Shapely 2.2.0. Open
  pictures: Wikimedia Commons and Openverse through the asset library (licence per item; share-alike kept and tagged
  `share-alike`; non-commercial and no-derivatives refused). Economics: the World Bank Indicators API (CC BY 4.0), Chart.js
  4.5.1, Vega-Lite 6.4.3 with Vega 6.4.0, Plotly.js 4.1.1. Diagrams: Mermaid 12.1.0 with its ELK layout (elkjs 0.9.3, used
  under EPL-2.0) and dagre 3.1.1. Law: India Code (the official repository of Indian law, read through its open REST API:
  an Act's record and every section) and the open Indian Supreme Court Judgments dataset (CC BY 4.0) read with pyarrow 26.0.0.
  Behaviour: PsychoPy 2026.2.4 (GPL; only `psychopy.data`, installed with `--no-deps` because its own pins need Python below
  3.13). Languages: Indic NLP Library 0.92 (with its two script tables pinned by hash), indic_transliteration 2.3.82, Noto
  Sans Devanagari (OFL). And the batch 3 BIE blocks (`bie-social-blocks`).
- **Adapters and sources:** `maps` (India's states with the area computed on an equal-area projection, Uttar Pradesh
  240,678 km² against the surveyed 240,928; towns and great-circle routes, renamed cities such as Prayagraj found under their
  older Natural Earth names), `economics` (Cobb-Douglas grid and the cheapest-mix path; World Bank series joined year by
  year, interpolated only inside a country's own range), `law` (a section is found by its **official title**, never by a
  number typed from memory: the BNSS flowchart's 173, 176, 193, 210, 249, 250, 251, 258 come from India Code; `listed_items`
  reads the four classes of criminal courts from section 6; the case card reads the bench, 13 judges for Kesavananda Bharati,
  from the judgment record), `behaviour` (the Stroop trial list by PsychoPy's TrialHandler; the PSI teaching-method logit by
  statsmodels: odds ratio 10.8, 95% CI 1.3 to 86.9, p = 0.026, n = 32), `language` (words, aksharas with the visarga kept on
  its akshara, IAST). Blender's FBX script can now join parts per parent group: Z-Anatomy's nervous system gives a brain of
  6 parts (4 lobes, cerebellum, brainstem) from 177 meshes. Commons and Openverse pictures are kept in the asset cache after
  the first fetch (Commons slows busy clients down with 429; a refusal is now named, not read as a missing file).
- **Web blocks:** india_map (region zoom, route with labels that avoid each other), timeline_build (D3 time scale),
  mermaid_build, flow_build (dagre; a "cycle" layout for process_cycle), tree_build (D3 tree), case_card, chartjs_build,
  vega_build, plotly_build, kinetic_text (aksharas build up, Roman and meaning below; the font loads from the asset library),
  experiment_flow; model_3d can colour named parts one by one with a legend.
- **Proof:** 16 more clips (51 in all); 15 rendered and passed in the cloud workspace. The 16th (`hist-archive-images`, Commons and Openverse) cannot run there: Wikimedia answers 429 to the workspace's shared address; the CI lane renders it. Wikimedia now serves scripts only its standard thumbnail widths (960, 1280 ...), so BIE asks for those. Seen on the contact sheets and fixed before the PR: Mermaid's nodes invisible and the
  diagram tiny (its own max-width and node ids), the dagre flowchart's text overflowing its boxes (now scaled as a whole),
  Vega-Lite adding zero to a shared scale, the brain's lobes not colouring (three.js writes glTF names with `_`), a route's
  town names on top of each other, neighbour countries looking like sea, a state count read from Natural Earth's outdated
  state/UT labels (now only "36 states and union territories").
- **Capabilities:** 40 of 42 have a tool; only Task 046's own `mnemonic_card` and `split_compare` are missing.
- **UGC NET and GATE map** (`bie/toolbox/exam_map.json`, on the toolbox page): the official lists of 25 October 2026 have
  **86 UGC NET subjects** (plus Paper I; the brief said 84) and **30 GATE papers**. Every one maps to the subject families
  and has at least one usable tool. Claude's reading of fit, for Navin to check: UGC NET strong 45, partial 37, general 4;
  GATE strong 22, partial 8. The gaps it names: fonts for other scripts (Bengali, Tamil, Telugu ..., Ol Chiki), right-to-left
  text (Urdu, Arabic, Persian, Kashmiri, Sindhi), CJK, music notation and sound, dance and human movement, 3D artefacts for
  archaeology and museology, phase diagrams, hull hydrostatics, building models.
- **Flagged for Navin, not blocked:** PsychoPy (GPL), India Code's terms (government content, free to reproduce with the
  source acknowledged), every map of India (check the boundary against the Survey of India before publishing),
  per-item licences of Commons and Openverse pictures.
- **Tests and CI:** core lane 41 tests (new: pinned Natural Earth, World Bank, India Code paging, Commons and Openverse
  licences and cache, a refusing API, the font and the Indic tables, the exam map); wrappers lane 11 more tests (maps on
  synthetic GeoJSON, economics, law with a parquet written in the test, PsychoPy, statsmodels, Indic NLP with the two tables
  as fixtures). The toolbox workflow renders batch 3 as a third matrix job.

## Task 046a · auzaar-ghar, batch 2: electrical, mechanical and civil, earth, astronomy, aerospace (25 October 2026)

Built in batch 2 (IMPLEMENTED; tools demo proven; nothing INTEGRATED into a lesson run yet, nothing ACCEPTED):

- **Registry:** 29 more entries (59 in all). Electrical: Schemdraw 0.23, Lcapy 1.26 (LGPL), ngspice 42 (apt), python-control
  0.10.2, scipy.signal (SciPy's pin). Mechanical and civil: PyNite 3.2.0, sympy.physics (SymPy's pin), CoolProp 8.0.0, CadQuery
  2.8.0 (OCP 7.9.3.1.1), scikit-fem 12.0.2 (added in place of FEniCS). Earth: GMT 6.5.0 (apt) and PyGMT 0.19.0 with the SRTM15+
  relief, ObsPy 1.5.1 (LGPL), pyGPlates 1.0.0 (GPL) with the Müller et al. 2019 plate model (CC BY 4.0), the USGS earthquake
  catalogue (public domain), Natural Earth through world-atlas 2.0.2 and topojson-client 3.1.0. Astronomy: Astropy 8.0.2,
  Skyfield 1.55, JPL DE421 (public domain), the Hipparcos catalogue, NASA's image library. Aerospace: AeroSandbox 4.2.10, JSBSim
  1.3.3 (LGPL). And the batch 2 BIE blocks themselves (`bie-science-blocks`).
- **Blocked, with what each needs:** FEniCSx/DOLFINx (no PyPI wheel; conda-forge, Docker or apt for the system Python 3.12) and
  OpenVSP (no PyPI wheel; its Python API ships only inside its own builds). Both stay in the registry so the gap shows.
- **Flagged for Navin's licence decision, not blocked:** pyGPlates (GPL), the Hipparcos catalogue (free for scientific use;
  commercial use under ESA's rules), the SRTM15+ relief (free with citation, no formal licence), NASA images (per item; an
  item naming a third-party copyright is marked).
- **Adapters** (`bie/toolbox/adapters/`): electrical (circuit pieces from Schemdraw; RC charging simulated by ngspice and
  checked against Lcapy's exact formula; step responses by python-control checked by scipy.signal), mechanics (PyNite beam
  checked against sympy.physics; CadQuery flange to .glb; CoolProp Rankine cycle; scikit-fem heat flow), earth (PyGMT relief
  and profile; ObsPy TauP rays; ObsPy example seismogram; pyGPlates reconstruction), astro (Skyfield orbits checked by Kepler's
  third law in Astropy; the sky from Hipparcos), aero (AeroSandbox aircraft and vortex-lattice lift curve; JSBSim Cessna 172
  climb with its own autopilot). Sources: USGS catalogue, the plate model (only its two named files are unpacked), NASA images.
- **Web blocks** (`blocks/toolbox/`): xy_lines (several series, legend box), circuit_build, beam_load, heat_plate,
  earth_section, world_points, plate_frames (coastlines filled as spherical polygons), orbits, sky_dome (read overhead: east on
  the left), flight_profile; model_3d can now spin the model under a fixed camera and fixed lights.
- **Proof:** 15 more clips (30 + 15 = 35 in all). Seen on the contact sheets and fixed before the PR: overlapping end labels
  (a legend box), a gap at the top of the saturation dome, dots drawn for series not yet started, a flange and an aircraft
  turning their dark side to the camera, coastline outlines with stray lines across the map, the sky chart drawn mirror-wise
  (east on the right), an Earthrise zoom that lost the Moon. After batch 2, 35 of 42 capabilities have a tool and 29 of them
  are shown in a clip; 7 are missing (batch 3, and Task 046's `mnemonic_card` and `split_compare`).
- **Tests and CI:** core lane 32 tests (new: USGS, plate model, NASA image sources with a fake network; proof demos must be in
  the tool's own batch); wrappers lane 30 tests (15 new, with ngspice and GMT installed; the astronomy test fetches DE421 once
  into the asset cache and reads three real Hipparcos lines from a fixture). The toolbox workflow renders batch 1 and batch 2
  in parallel (a matrix), the bridge with batch 1.

## Task 046a · auzaar-ghar (toolbox), batch 1 (25 October 2026)

Task card (Navin ke liye, 25 October 2026):

- **Kya banega:** BIE ka auzaar-ghar. Ek register (`bie/toolbox/registry.json`) jisme har library, tool aur asset source ka naam,
  version, licence, kaam (capability) aur status likha hai; ek "resolver" jo scene ki zaroorat (jaise "cell sheet 3D", "ECG
  trace", "protein 3D") se sahi tool chunta hai, aur jo kaam koi tool nahi kar sakta use "missing" likh deta hai; do render raaste
  (web: Remotion + three.js aur baaki JS libraries; offline: Blender aur Manim) aur unke beech ek pul. Har tool ka 3–5 second ka
  chhota proof clip, BIE ke code se bana.
- **Aap kya dekhenge:** toolbox page (`docs/toolbox/TOOLBOX.md`: subject → capability → tool → status), har clip aur uski
  contact sheet, kya blocked hai aur kyon, aur "missing capabilities" ki list.
- **Kaise pata chalega ki ho gaya:** har tool ka clip ya test CI me pass; status word ek daava hai jo demos lane har baar check
  karta hai (demo fail to CI laal); sab CI green; teen PR (batch 1, 2, 3). Kharcha ₹0.

Built in batch 1 (IMPLEMENTED; tools demo proven; nothing INTEGRATED into a lesson run yet, nothing ACCEPTED):

- **Registry, schema, loader** (`bie/toolbox/registry.json`, `registry.schema.json`, `registry.py`): 30 tools: the web stack
  (Remotion 4.0.536, @remotion/three, three 0.186.1, React Three Fiber, drei, KaTeX, D3, 3Dmol.js, Mol*, matter.js, cannon-es,
  BIE's own blocks), Blender 5.2 (bpy), NumPy, SciPy, SymPy, Manim, statsmodels, NetworkX, Biopython, NeuroKit2, RDKit,
  Cantera, trimesh (added: joins BodyParts3D's OBJ files into one glTF), and the asset sources Servier Medical Art, Z-Anatomy,
  BodyParts3D, NIH 3D, RCSB PDB, PubChem. Every version is pinned (npm as of `tools/npm_before.txt`; PyPI extras
  `toolbox-core/-stats/-bio/-chem/-mesh/-manim/-blender` in `pyproject.toml`); every licence read from the project's own page
  on 25 October 2026. Flags for Navin's later licence decision, nothing blocked: Remotion (own licence: free up to 3 people),
  Blender (GPL, used as a separate program), Z-Anatomy (CC BY-SA 4.0, share-alike), BodyParts3D (CC BY 4.0 on its licence
  page; older files said CC BY-SA 2.1 JP), NIH 3D and PubChem (licence per item, recorded per asset).
- **Capabilities and resolver** (`capabilities.json`, `resolver.py`): 42 capabilities tied to the content types and the 045d
  visual verbs; `resolve(capability, subject, level, path)` returns the drawing, computing and asset tools with a fallback
  path; a capability nothing provides is logged (`BIE_TOOLBOX_MISSING_LOG`). After batch 1, 24 capabilities have a tool
  and 17 of them are shown in a proof clip (the page has a clip column per capability, because a status word is per tool);
  7 have a tool but no clip yet (`board_build`, `concept_arrow`, `kinetic_caption`, `table_build`, `timeline`: Task 039's
  2D blocks; `machine_part_3d`, `vector_field`: batch 2); 18 are missing (batch 2/3 tools, or blocks planned in Task 046:
  `mnemonic_card`, `split_compare`).
- **Web path:** a block registry (`bie/brain/video/blocks/registry.ts`, layer type `block`) and seven toolbox block files
  (`blocks/toolbox/`: 3D cell sheet with particle flow, glTF model with glow and zoom, cannon-es collision, equation steps that
  refuse an unchecked step, function graph, ECG and waves, falling body, matter.js bodies, BFS on a graph, reaction with
  kinetics, 3Dmol.js and Mol*). The preview renderer gained `delayRender`/`continueRender` (a frame waits until its model is
  loaded and drawn), a Remotion-faithful `Easing`, a ThreeCanvas stand-in, SwiftShader WebGL, and a separate toolbox bundle,
  so the core bundle the brain uses stays as small as before.
- **Bridge proof:** `bie/brain/video/remotion/` (Root.tsx + render.mjs) renders the same blocks with real Remotion
  (`@remotion/bundler` + `@remotion/renderer` 4.0.536, Chrome Headless Shell, `gl: swangle`); `tools/toolbox_demos.py --bridge`
  compares its frames with the preview's (local: mean difference 0.0 on all six frames). It found a real bug on the way: the
  preview's `Easing.inOut` did not follow Remotion's API (NaN camera in real Remotion); fixed.
- **Offline path:** `bie/toolbox/adapters/` (physics, maths, graphs, biology, chemistry, meshes, blender, manim) return plain
  JSON; Blender and Manim run as separate processes (`bie/toolbox/blender/*.py`, `bie/toolbox/manim_scenes.py`).
- **Asset sources** (`bie/toolbox/sources.py`): fetched on demand into `BIE_ASSET_CACHE` (outside git) and recorded in the
  asset library with licence and credit; non-commercial or no-derivatives licences are refused, share-alike is tagged.
- **Proof:** 20 demo clips (`bie/toolbox/demos.py`; `tools/toolbox_demos.py` renders, takes six stills for a contact sheet,
  checks not blank / moves / 3–5 s and the installed versions against the registry, and checks every status claim);
  `tools/toolbox_page.py` writes `docs/toolbox/TOOLBOX.md`. Seen on the contact sheets and fixed before the PR: equation steps
  were typeset after SymPy had simplified them (three identical lines), a fitted line drawn by its two end points appeared at
  once, Z-Anatomy parts lost their place when unparented, a Manim clip began on an empty frame, Mol* drew crystal water
  (and took 583 s; 330 s without it and the screen-space effects), the 3D collision missed the tower. A stack of boxes is
  chaotic in cannon-es (a 1e-9 shift can leave it standing), so the collision numbers were swept with jittered starts until
  the tower fell in 8 of 8 runs.
- **Tests and CI:** `tools/run_task046a_tests.py` (lane core: 29 tests, no heavy libraries, also run by the canonical gates;
  lane wrappers: 15 tests in `tests/toolbox/test_wrappers.py`, one per wrapper, with Blender and Manim really run; that
  folder is outside the canonical gate's discovery because its libraries are toolbox extras, found when the first PR run
  put the file in `tests/` and the canonical gate, which forbids skips, errored on the missing libraries); workflow `BIE Task046a Toolbox` (`.github/workflows/toolbox.yml`, path-filtered,
  so the canonical gates are not slower): core, wrappers, and demos (all clips + the bridge + the page, uploaded as an
  artifact for 30 days). The Task 039 lane (248) still passes with the changed preview renderer.

## Task 045d · teaching soul (24 October 2026, PR #60 merged at `ce0e3491`)

Navin's decisions of 24 October 2026 (binding; `docs/vision/TEACHING_SOUL.md` summarises them): BIE is the link between the
learner and the book, like a teacher; it never just reads the line out. The level follows the book's own text combined with
the course setting, and a disagreement is his to settle. Two layers like a film: the writer layer (understanding, plan,
script) follows the level; the presentation layer (director, blocks, render) is the same skilled quality for every learner.
The video stays code-rendered through two routes (A: three.js in Remotion; C: Blender-made or licensed 3D models animated by
BIE code), planned in ROADMAP Task 046 with a head-to-head and a merge path. Every explanation his verdict locks is reused.

Built (IMPLEMENTED, offline with the fake AI; the Task 045 lane is green):

- **Section 1 unpack** (`bie/brain/soul.py`, `understanding.py`, schema `bie.brain.understand-page/3`, naksha `/2`): every
  teachable item carries terms (plain meaning in simple Hindi, everyday image), a why chain from a need with its basis, an
  example or place, a consequence, a visual verb and the level's extra; code check S1-15 (at least one element, every why
  step with its basis, the chain within the level); the unpack reaches the script maker and the naksha.
- **Level profiles** (`bie/brain/level.py`, `rulebook/level_profiles.json`: school, neet_11_12, upsc_pcs, revision; Navin
  edits the file): chosen from the course setting (`--level`, or the words of learners and exam) and checked against the
  book's text (markers, then the share of long words); a disagreement stops the run before any call (`stopped: level`) and
  asks Navin; `--level <id> --trust-level` records his answer in every record. The tissue chapter reads as senior secondary
  and fits UPSC, so the rerun needs no question.
- **Section 2** (`lesson.py`, schema `bie.brain.lesson-script/3`): pattern steps flexible with a stated reason
  (`skipped_steps`), the family pattern for a classification (`content_types.json` 2026-10-24.1), one recap per part;
  code checks S2-07: dohraav pakad (a beat whose English content words are 60% or more the book's own with no yaani / why /
  example / contrast marker goes back), clipped verbless sentences, a question at every topic's opening, duplicate recaps;
  the `dohraav` measure per video and per run, and `tools/dohraav.py` for any run folder.
- **Teacher example bank** (`rulebook/teacher_examples.json`: 7 opening steps, 10 methods with examples, Navin's own
  absorptive/secretive example and "slender yaani long aur narrow") in every page and script prefix; **explanation
  library** (`bie/brain/explanations.py`, `rulebook/explanations.json`: Navin's three entries) looked up by term for every
  page and script, locked only through `tools/lock_explanations.py` after his verdict.
- **Rulebook** `vision-2026-10-21@2026-10-21.12`: G-06, G-07, S1-15, S2-07, S3-06; the rulebook version counts the three
  new data files. **Benchmark** `rulebook/benchmarks/epithelium_animation.json` (12 rules, 22 shots, the blocks of Task 046).
- **Guard:** both saved sets still pass; the new rules show as waived rule changes (S1-15, S2-07, the family pattern), the
  regression guard reads each rulebook component's version; `tests/test_task045d_soul.py` (30 tests) joins the Task 045 lane.
- A detector fix on the way: the Hindi verb check glued the danda to the verb ("… है।" read as verbless); fixed and tested.

Run after merge (Navin's brief): the tissue understanding (14 pages + map) and the script again on the VM, maker Codex,
Gemini checker, cap ₹200 in all; then old v2 against new v2 side by side and the dohraav number before and after.

## Task 045 · understanding and script on the tarazu (22 October 2026, PR A merged)

- **Seekh → BIE from job 2 and Navin's decisions (23 October 2026; IMPLEMENTED, merged with PR #53 at `0ca5763d`, measured offline; `docs/roadmap/SEEKH_LOG.md` entry 2):** Hindi brackets (1,909 everyday words with their forms, 94 fixed phrases; code removes needless brackets before the checks; job 2's 838 hard-word problems → 0, in sample); a patch round keeps the unit's notes; narration 6–8 minutes per book page with a plan and a script check (topic videos 84–112 minutes for the tissue chapter; at least 3 minutes per topic video, approved by Navin); only book-answered questions are mandatory; only directly needed prerequisites, no chains (more than 8 is a warning the maker answers with a reason, not a cap; Navin, 23 October 2026; rulebook `2026-10-21.11`), an older map trimmed once by a new connect task `trim_prerequisites` (`bie/brain/prerequisites.py`), taught in one "pehle yeh jaan lo" video `v0` (5–8 minutes); S1-13 (typo kept, "Cartiage [Cartilage]") and S1-14 (one answer, one basis); rulebook `vision-2026-10-21@2026-10-21.11`; regression sets list rule changes instead of hiding them (job 1's map: 30 prerequisites, upgraded by the trim); the lesson estimate is measured from job 2; a cache probe mode (`cache-probe`, cap ₹10). Task 045 lane: 377 offline tests.
- **Seekh → BIE from job 1 (23 October 2026; IMPLEMENTED, measured offline; live effect on the next run, see `docs/roadmap/SEEKH_LOG.md`):** type detection reads a restarted list (a. b. c. then a.) as a new list and a line ending in a colon as a hint; the page and map instructions now say up front what sent job 1's round 1 back (options of a question on the previous page, concepts typed "none", answers that only repeat the item); the checker reads compact JSON (−16.7% of the answer tokens it reads, o200k); lean Codex calls switch off Codex's own agent prompt and tools (−8,000 input tokens per call on a real page request, measured against a local stand-in server; the model can no longer run commands or browse); job 1's passed work is a regression set that every change must keep passing (`tests/fixtures/passed_outputs/`, `tools/passed_outputs.py`); `tools/seekh_measure.py` measures every run the same way; readable pages show rupees.
- **PR B tooling (23 October 2026):** the script step resumes like page reading (`--resume-from` an earlier lesson run: the plan and every script that passed are reused when the chapter map is the same and they still pass today's checks; anything else runs again), so the plan's own limit or the cap never loses work. Readable pages: `MAP.md` is now the map itself (teaching order, concepts, relations, engine checks, type differences, a pass/fail table per page) and every item with its teacher questions moved to `PAGES.md`; every video also gets its own page `scripts/<video id>.md`; `tools/render_run.py` rebuilds these pages for an earlier run folder (into `readable/`, the run's own files stay as written).
- **PR #45 merged** at `c08d51cb` after all 6 checks that ran on its head `7d8d9d2b` passed (Post-DIR canonical, Section 16 combined, Section 18 canonical-regression, native-render and section16-regression, Task038 offline with the Task 045 lane; the live job is skipped on pull requests).

What is built (all offline; nothing live yet):

- **Content types in code** (`bie/brain/content_types.py`): before the maker reads a page, BIE proposes a type for every native text block from the hints in `content_types.json` (keywords, patterns, and list context: a numbered list takes the type of the line that introduces it). The maker sees the proposals on its card, uses BIE's nine type ids (Section 1 schema `bie.brain.understand-page/2`; old types convert through `legacy_types`) and gives a `type_note` when it chooses another type. Every difference is recorded per item (agree, explained, disagree, weak, silent, role, follows parent); an unexplained strong difference goes back to the maker. Required questions per type are enforced for every teachable item (before: only process, comparison and classification). Hints were refined on the tissue chapter (`content_types.json` 2026-10-22.2; no type, question or pattern changed).
- **Naksha** (`bie/brain/naksha.py`, `bie.brain.naksha/1`): built once from the chapter map, written as `naksha.json`: one row per teachable item `[id, type, page, short text, required questions (kya, kaise …), exam]`, concepts, links (`pre`, `part`, `kind`, `cause`, `compare`, `seq`, `example`, `test`, `ref`), teaching order, prerequisites, sha256. Later sections get slices only (own items plus one row per related concept). Measured on the old tissue map (run 39627682253, converted): 469 items, 71 concepts, 399 links, 80,463 characters, about 23,500 tokens, against about 204,000 tokens for the full chapter map; a 12-item slice is about 860 tokens, the concept layer about 1,500. Tokens are estimated at 3.43 characters per token, measured from that run's connect call; the ledger has real counts.
- **Task cards** (`bie/brain/cards.py`, schema moved to `bie/brain/task_card.schema.json`): every Section 1 and 2 call is a fixed prefix (header, role and course, rule texts sorted by id, content types, output schema, how to answer) plus a compact card. The prefix is the same bytes for every page or video of a run, hashed on the card and in every process record; the runner refuses a step whose card does not match the prefix it would send. Cards are checked before anything is sent (schema, prefix, task of the section, locked rules, required questions per part, known ids); `must_cover` is checked both ways after the answer. Example: `docs/roadmap/task_card.example.json`, the real read_page card of tissue page 3 built by code.
- **Old engines merged as checks** (`bie/brain/engines.py`, decisions in `engines.DECISIONS` and TARAZU): KI replaced and retired (the lexical producer `bie/productization/candidates.py`); its coverage, orphan and definition QA checks the map. PR producer (`pr_reasoning.py`) replaced and retired; its graph checks prerequisite circles, the teaching order (with a valid order proposed) and redundant links. RE extended: cause circles and dated links that go back in time. PED planner (`pedagogy_plan.py`, `pedagogy_slice.py`) replaced and retired; its QA checks objective coverage, load per beat, prerequisite coverage and length. Retired files stay (the ledgers fail on a deleted working file); a test proves no brain code imports them; the 11-stage technical pipeline keeps them as regression fixtures until Task 051 moves its durable run onto the brain.
- **Section 2 on the card** (`bie/brain/lesson.py`, `bie.brain.lesson-script/2`): the plan card carries the concept layer only; a script card carries its video's items grouped by concept and type, with their required questions and a naksha slice. The script fills the universal frame for every part (process, how, when, conditions, atmosphere; a process, timeline or cause part may not skip its key fields) and tags every beat with its part and teaching-pattern step; code checks every step, `must_cover` both ways, Navin's Hinglish (Devanagari share, digits 0-9, no sentence over 40 words) and the PED checks. PYQs get their own part and are answered as exam tips.
- **Rulebook** `vision-2026-10-21@2026-10-21.8`: S1-08 names the nine types; new S2-06 (frame and teaching pattern), from Navin's Task 045 brief.
- **Same-model checker** (`--reviewer-model same`, workflow `providers` `google,google:same`): only for a key that allows one model; marked `same_model_temporary` and "kamzor jaanch" in every record and page. A same-company checker on another model stays `same_company_temporary`.
- **Tests:** `tools/run_task045_tests.py`, 328 offline tests (33 new in `tests/test_task045_cards.py`), plus the fake chain on four real tissue pages (all pass; the fake proves plumbing, not quality).

Measured offline on the tissue PDF (₹0):

- Type check against the old run's AI types (converted): 15 agree, 10 strong differences that would go back to the maker, 11 weak differences, 153 items the code has no hint for, 340 rows, labels or questions that follow their parent or role. Examples: the four lines under "There are mainly four different types of tissues" (AI: fact, code: classification); "Collagen fibres … made up of fibrous protein" (AI: fact, code: structure); "Xylem consists of tracheids, vessels …" (AI: classification, code: structure).
- Prompt size per page, Section 1: old system prompt about 2,240 tokens plus about 700–1,050 for the page text; new fixed prefix about 4,350 tokens (cacheable, the same for every page) plus card and blocks about 430–2,090 (about 1,030 on average). The card makes the input bigger; output (10,800–18,200 tokens per page in run 39620281561) still decides the cost.
- Reuse: none of the 10 pages that passed in run 39627682253 passes today's checks (their items lack the required questions of their type), so the tissue chapter is read again in full.

Status words: Sections 1 and 2 on cards, the naksha, type detection and the engine checks are IMPLEMENTED (fake AI only). Nothing from Task 045 is INTEGRATED or ACCEPTED until the live runs and Navin's verdict.

PR B (only after Navin's yes): live runs on the Gemini key, maker `google/gemini-4-argon`, a same-company checker marked "kamzor jaanch"; nothing locked as accepted. Estimate for the tissue chapter (14 pages, price-table basis): understanding about ₹319 (page reading ₹240, map ₹79), script about ₹199 (assumed, not measured); a ₹30 cap per run covers about 1–2 pages, so the chapter needs several stop-and-resume runs or a higher cap (Navin decides). Then one chapter each of History, Geography, Polity, Economics and Physics/Maths (Navin sends the PDFs).

## Task 044c · Sign in with ChatGPT feasibility (22 October 2026, report only)

- **Report:** `docs/roadmap/SIWC_FEASIBILITY.md` (8 questions, every rule quoted with its URL, status words confirmed / confirmed (excerpt) / not confirmed / unknown). No code, no sign-in, no model call, ₹0.
- **Verdict: conditional (shart ke saath).** The plan could power BIE's maker only from a machine Navin alone controls. His own laptop is the only place the SIWC terms clearly allow; a VPS he alone controls is described by the developer docs but conflicts with the terms sentence "Any persistent storage of Authentication Tokens must be local and under the user's control, not in a remote or managed environment." (excerpt; the terms page returns HTTP 403 to our tools). GitHub Actions, Codespaces and managed VPS plans are not allowed.
- **Plan change: none.** The Codex route (Task 044) stays primary: it enforces the JSON schema (SIWC does not document one), signs in on the server itself and shows plan usage. SIWC uses the same ChatGPT/Codex usage pool.
- **Unknowns:** JSON-schema output, whether BIE counts as open source without a LICENSE, whether a commercial personal project qualifies, how far a suspension would reach.
- **Next (all optional, Navin's choice):** a one-time probe on his laptop (designed in the report, not written), OpenAI's interest form to ask about a rented server; the Codex machine decision is still open.

## Task 044 · ChatGPT Pro maker (22 October 2026)

- **PR #43 merged** at `9fbb256a` (code, tests and the machine kit).
- **The machine (22 October 2026):** Navin chose **Hostinger KVM 2 in Mumbai** (Ubuntu 24.04), not AWS Lightsail: about ₹1,300 a month, a 1-month term with a 30-day refund. He ran `setup.sh` and `sudo bie-setup` himself: Gemini key set on the machine only, Codex signed in with his ChatGPT Pro plan, the GitHub deploy key added (approved by adding it), the 2-minute poll timer active, plan usage 0% before any job.
- **Step 5 live test (23 October 2026, job `t044-step5-tissue`, results `blindtest-results:runs/vm-t044-step5-tissue-brain-understand/`):** tissue pages 1, 7, 11 and 13 on the machine, maker Codex (`gpt-6.1-sol` through ChatGPT; Codex reports the plan as `prolite`), checker Gemini 4 Argon (AICredits, another company), cap ₹30, 29.7 minutes.
  - **All 4 pages passed** (they had failed in run 39627682253): pages 1 and 7 in one round, 11 and 13 in two; 185 items (171 teachable), 536 teacher questions (199 deeper why/how, 237 marked outside the book). Type check: 6 agree with the code, no unexplained difference; 43 items the code had no hint for (mostly read from the image).
  - **Chapter map: stopped by the cap.** Its first round had three code problems (a question link to a non-question item, an unlinked question, a concept typed `none`); the maker fixed them, and the checker call of round 2 (projected ₹14.57) would have crossed the cap, so it was not sent. Passed pages are kept; a resume can finish the map.
  - **Gemini spent ₹23.55** (ledger estimate, not the bill): preflight ₹0.39, page checks ₹23.16 for 5 checker calls (85,563 tokens in, 5,148 out; about ₹4.6 a call, ₹5.8 a page). The measured-basis estimate was ₹14.6; the checker reads more since Task 045.
  - **Codex (₹0, the plan):** 6 page calls (159,134 tokens in, 43,136 of them cached; 68,687 out; 32 minutes of call time) and 2 map calls (71,142 in, 26,865 out); the weekly plan window went from 0% to 1%.
  - **Status words:** the Codex maker route is INTEGRATED for Section 1 page reading (real machine, real ChatGPT plan, real pages, real downstream map step); the map is not checked yet. Nothing is ACCEPTED.
- **PR #42 merged** at `afe169b1` after all 7 checks on its head `f432e245` passed.
- **Hosting decision** (`deployment/codex-vm/README.md`), from OpenAI's docs read on 22 Oct 2026 and the Codex CLI itself (0.162.1, installed in the cloud workspace without signing in):
  - ChatGPT sign-in for automation is for trusted private machines only ("Do not use this workflow for public or open-source repositories"); this repository is public, so its GitHub Actions never sign in. The Anthropic and GPT API key secrets were removed from the live workflow step.
  - Codex cloud: possible only as a slow hand-off (an agent inside a cloud task, started from the ChatGPT app, an `@codex` comment or `codex cloud exec`, which itself needs a signed-in machine; results as diffs or PRs; a new task per remake; no enforced output schema; image reading cannot be checked; same 5-hour plan window). Judged not reliable or automatic enough.
  - **Chosen: a small private machine running `codex exec`.** Recommended AWS Lightsail Mumbai, 2 GB, $12 a month (about ₹1,340 with GST); budget option $7 (about ₹780); DigitalOcean Bangalore similar; Hetzner about ₹650–700 (no India location); Oracle free tier not recommended (idle machines are reclaimed). Nothing bought; Navin decides.
  - JioPC: not suitable (shuts down 15 minutes after disconnect).
- **Codex maker route** (`bie/model_gateway/live/codex_client.py`): one `codex exec` per maker step: instructions and task on stdin, page images as `--image` files (the CLI accepts them; the flags were checked against the real CLI, which reached OpenAI and returned 401 without sign-in), the JSON schema as `--output-schema`, read-only, ephemeral, empty working folder, no API key and no other secret in its environment. Usage per call: `billing: subscription`, Codex's token counts, time; no rupees. A used-up plan window is a new error kind `plan_limit`, never retried; the run ends `stopped: plan limit` and `--resume-from` continues it.
- **Cost guard update:** preflight checks Codex sign-in first (no call if signed out), reads the plan's usage windows (`account/rateLimits/read` through `codex app-server`) before and after the run, sends a tiny call per route and, for sections that read pages, a picture of the number 47 that each model must read (images are never dropped silently). The rupee cap counts only the Gemini checker; the estimate drops the maker's share when the maker is on the plan. SUMMARY.json adds plan usage before and after, subscription calls, tokens and minutes, and seconds per page.
- **Codex as the checker too (Navin, 27 October 2026, in his words: "Google key ke bharose mat baitho na hi paid call; codex ya claude ke subscription ka use kar lo review purpose ke liye hi karna hai na, kyuki mujhe yeh abhi chahiye"):** the free Google key's daily quota ran out on the Money chapter's first run (VM job `t046c-money-understand`, 4 of 20 pages) and a one-page probe confirmed it, so `--reviewer codex` now runs the checker on the ChatGPT plan through the Codex CLI as well (₹0; its own `CodexExecClient`, a fresh call). With `--maker codex` it needs `--reviewer-model`: another plan model, or `same` (the maker's model in a fresh call, the weakest check, `same_model_temporary` in every record; nothing it passes is ever locked as accepted). The VM job field `reviewer: codex` (+ `reviewer_model`), the estimate counts a subscription checker at ₹0, the preflight checks the sign-in on both routes. Google (free key, when its quota is back) and the other-company rule remain the default; this is the "abhi chahiye" route.
- **Private-machine kit** (`deployment/codex-vm/`, `tools/codex_vm.py`): `setup.sh` (no secrets), `sudo bie-setup` for Navin (Gemini key, GitHub deploy key, `codex login --device-auth`), a 2-minute timer that runs jobs from `jobs/<id>.json` on the `codex-jobs` branch through `tools/run_brain.py` and publishes to `blindtest-results`. Security note for Navin's approval: the deploy key can write to the whole repository; branch protection comes with Phase 4.
- **Tests:** `tools/run_task044_tests.py`, 295 offline tests (22 new in `tests/test_task044_codex.py` with a fake `codex` executable, `bie/brain/fake_codex.py`): success with images and schema, schema error, plan-limit stop and resume, sign-in missing, vision check, no secret reaching Codex, subscription billing, the VM job runner end to end against a local git remote. The Task 043 cap test now counts the vision preflight calls.
- **Live test (pending the machine):** brain-understand on the tissue chapter resuming from run 39627682253 (pages 1, 7, 11 and 13 run, the other 10 reused), maker codex, checker Gemini 4 Argon, `max_inr` 30; the chapter map is rebuilt over all 14 pages for Task 045.
- **Status words:** the Codex route is IMPLEMENTED (offline, fake CLI); nothing live yet.

## 23 October 2026 · mixed-script narration (Task 045b)

- **Navin's teaching decision:** narration is mixed script: Hindi words in Devanagari, English words (above all the book's terms) in Roman, as in "आज हम tissue के बारे में पढ़ेंगे". A Hindi word that is not a simple everyday word gets its English word in brackets right after it, "सतह (surface)"; the screen and subtitles show the bracket, the voice says "सतह, यानी surface".
- **Built:** `bie/brain/rulebook/simple_hindi.json` (version 2026-10-23.1, 778 seed words; Navin adds words and the version goes up; it counts in the rulebook version); `bie/brain/hinglish.py` (simple-word test with common endings and spelling variants, the bracket check, Roman-written Hindi check, `voice_text` and `subtitle_text`). Section 2 checks every beat with it; the script prefix carries the rule and the word list; `lesson_plan.json` beats get `subtitle` and `voice`, and SCRIPT.md shows the voice line. The check never asks for an English term in Devanagari or a Hindi word in Roman.
- **Rulebook** `vision-2026-10-21@2026-10-21.9`: S2-04 states the mixed-script rule.
- **Status:** IMPLEMENTED (offline tests, 333 in the Task 045 lane). The seed list is a first guess at "simple everyday Hindi"; the live scripts will show which words it misses, and Navin decides additions.

## 22 October 2026 · build freedom (Task 044d)

- Navin decided that Claude may write any amount of code and add any tools, resources, code libraries and subject-specific libraries (for example SciPy, RDKit, three.js) that make BIE better, even beyond the tarazu, as long as everything joins the existing BIE (use, extend, or replace and retire explicitly) and nothing becomes a parallel system. Recorded in `CLAUDE.md` under "Engineering rules (binding)" as "Build freedom", with its guardrails: licence check, pinning and tests for every library; real-book proof and honest status words for every part; the cost guard and "reuse, do not duplicate" still apply; security-sensitive changes, budget and quality verdicts stay Navin's to decide.

## 22 October 2026 · what was agreed

- **BIE is the system between Navin and AI** (binding): it understands the whole book (chapter map), tells the AI exactly what to make through compact task cards and fixed output formats, checks every output with code and a second AI, builds video, game and notes with its own engines (the AI only fills data), and records and locks whatever passes. Not a prompt wrapper; lesson content only by BIE.
- **Order:** every section meets the five points (the tarazu), merging the brain into the old BIE code (one BIE) → ChatGPT Pro early → after each section, tissue + 4–5 chapters of other subjects judged by Navin → one-button software → only then heavy vs light method, cost optimisation, own model.
- **Cost target:** ₹50–300 per book; optimisation later, a cost guard now.
- **Tasks 043–052** are in ROADMAP. Task numbers in STATUS entries written before 22 October follow the old plan (old 043 Voice is now 047, 044 Render 048, 045 Game 049, 046 Notes 050, 047 Review 051–052).

## Task 043 · cost guard, tarazu, content types, task card (merged in PR #42)

- **PR #41 merged** at `c8853eb2` after all 7 checks on its head `0287f668` passed (Post-DIR canonical, Section 16 combined, Section 18 canonical-regression, native-render and section16-regression, Task038 offline; the live job is skipped on pull requests).
- **Cost guard ("pahra")** (`bie/model_gateway/live/budget.py`, `bie/brain/cost.py`, `tools/run_brain.py`, workflow input `max_inr`, default 300):
  - Preflight: one tiny structured call per route before any work (plus the AICredits wallet, which answered "not found" at `/v1/credits`). Any failure stops the run as `stopped: preflight` with a `pahra preflight` annotation; keys are redacted.
  - Estimate: "Andaaza ₹X, seema ₹Y" per section from the page count. Section 1 uses the measured Task 039 ledgers ($0.181 per page reading, $0.06 per page for the chapter map, GPT-6.1 Sol + Gemini 4 Argon); Sections 2–7 are marked "assumed" until a live run measures them. Rate ₹94.59 per dollar (AICredits, 20 Oct).
  - Hard cap: checked before every call, including retries and repairs; a call whose projected cost would cross the cap is not sent, passed work is kept, the status is `stopped: budget`, and the chain does not start the next section.
  - Balance errors (HTTP 402, `insufficient_quota`, "Budget Exceeded", "Insufficient Balance") are a new error kind, never retried; they stop the run (OpenAI's quota error was retried four times before).
  - After the run: rupees per section and per page in `SUMMARY.json`, with the note that it is a price-table estimate and a `real_bill_inr` slot; `docs/roadmap/COST_LOG.md` is where dashboard amounts are written.
  - Records name the maker and reviewer models and the reviewer's independence; a same-company checker is allowed only with another model and is marked `same_company_temporary`.
  - Ledger rows now carry `cached_input_tokens`, so provider caching is measured.
- **Tests:** `tools/run_task043_tests.py`, 273 offline tests (27 new in `tests/test_task043_pahra.py`, plus the Task 039 and 038 lanes): cap-stop keeps passed pages (pages 1–2 passed, page 3 stopped, ledger ₹1,800 under a ₹1,850 cap), preflight-stop runs no section and leaks no key, every preflight route judged on its own, estimate numbers, rupees per section, same-company checker records, content types and the example task card.
- **Live (all on the Gemini key via AICredits):**
  - Probe (run 39734021966, 39734670129, free): the platform lists 439 models, 30 of them Gemini, with prices; the key's own model list shows the same 30.
  - Live smoke, `max_inr` 5 (run 39734293232): maker Gemini 4 Argon, checker Gemini 3.1 Pro Preview, one page. Estimate ₹23.47 for one page against the ₹5 cap (warning shown). Preflight stopped the run: "This API key is not permitted to use model 'google/gemini-3.1-pro-preview'". Spent ₹0.08 (the maker's preflight call).
  - Access check (run 39735198529): of Gemini 4 Argon, 3.1 Pro Preview, 2.5 Pro, Pro Latest, 3.8 Flash and 3.5 Flash, the key allows only **Gemini 4 Argon**; the five refusals cost nothing. Spent ₹0.08.
  - Proposed pair (temporary, same company, marked in records): maker `google/gemini-4-argon` ($2 / $10 per million tokens, reads images), checker `google/gemini-3.1-pro-preview` ($2 / $12, reads images, a different generation). Needs Navin to allow the checker model on the AICredits Gemini key.
- **Batch and caching (research, not built):** AICredits documents no batch API and no batch discount (its pricing page names a "Batch tier" without a figure). It passes provider caching through at cached-input prices: Gemini 4 Argon cached input $0.10 instead of $2.00 per million (api.aicredits.in/api/models); OpenAI cached input at half price; Claude only with `"cache": true` (reads 0.1×, writes 1.25×, 5 minutes). Gemini caches repeated prefixes implicitly on 2.5 and newer models (hits not guaranteed). Google's own Gemini API has a Batch mode at 50% of the price (up to 24 hours) and caching at a 90% discount, but only with a direct Google key, which BIE does not use now. The task-card design puts all fixed text first so caching can hit (Task 045 measures it).
- **Tarazu audit:** `docs/roadmap/TARAZU.md` (18 old sections, the productization glue and 12 brain modules). Biggest gaps: review and lock not built (051, 052); no voice (047); no real render or player (046, 048); game half built with two runtimes and no book world (049); understanding not yet on content types and task cards (045).
- **Content-type map:** `bie/brain/rulebook/content_types.json` (version 2026-10-22.1, design): process, structure, classification, comparison, timeline, cause-effect, facts and numbers, figure, definition; for each the questions (kya, kyun, kaise, kab, kaun, kahan, tulna, saboot, nateeja), teaching pattern, video blocks, game mechanic, notes infographic and code-side detection hints. The rulebook version now includes it (`content_types@2026-10-22.1+vision-2026-10-21@2026-10-21.7`).
- **Task card:** `docs/roadmap/TASK_CARD.md`, schema `docs/roadmap/task_card.schema.json`, example `docs/roadmap/task_card.example.json` (a lesson card for page 3 of the tissue chapter with real item ids, about 800 tokens).
- **Status words:** the cost guard is INTEGRATED for preflight (a real provider refusal stopped a real run); the cap-stop is proven offline only, until the second Gemini model is allowed. Nothing is ACCEPTED.

## Tasks 039–042 · the brain (merged in PR #41 on 22 October 2026)

- **Vision rulebook** (`bie/brain/rulebook/vision-2026-10-21.json`, `bie/brain/rulebook.py`, version 2026-10-21.5, 34 locked rules): Navin's agreed vision, each rule an instruction for the maker and a yes/no check for the reviewer. Changes since the first version, all forced by live runs or added sections: G-03 now asks for brief decision notes instead of written "thinking" (a provider blocked the first wording, see below); R-01 gives reviewer findings a severity and judges at the learners' level; S1-07 keeps outside explanations at textbook level without absolute words; S2-03–S2-05 (prerequisites taught, Navin's spoken Hinglish, true coverage claims); S3-03–S3-05 (word-timed visuals, anatomy-level descriptions, interactive moments).
- **Section runner** (`bie/brain/runner.py`): maker AI writes brief notes and its output → BIE code checks → independent reviewer on another provider with the rulebook checklist (blocking or minor findings) → remake as a patch of only the changed parts, at most 3 rounds → one process record per step (each round's notes, output, patch, problems, reviewer findings, models, tokens, cost; failed rounds marked "avoid"; images by hash only; `navin_verdict` left for Navin).
- **Gateway:** page images in messages for all four clients; output cap; streaming (server-sent events) for all four clients, used by every brain run.
- **Section 1** (`bie/brain/understanding.py`, `bie/brain/pages.py`): two-eye page reading (DI native text blocks plus a rendered page image), items with locations, question-based teacher understanding with depth and book/outside basis, code checks, chapter map (concepts, relations, prerequisites to teach, cross-references, question links, teaching order); `--resume-from` reuses passed pages of an earlier run.
- **Section 2** (`bie/brain/lesson.py`): video plan from the chapter map, then one spoken Hinglish teacher script per video in beats; each beat claims the items and teacher questions it answers; code checks full coverage and Devanagari Hinglish.
- **Section 3** (`bie/brain/director.py`): scenes per video with the universal frame, subject style, anatomy-level element descriptions, camera moves and actions cued to the exact spoken word, visual mathematics, pause questions and tap-to-explore.
- **Task 042 start** (`bie/brain/assets.py`): Wikimedia Commons search keeping only licences allowed in a paid course (public domain, CC0, CC BY; CC BY-SA only if Navin allows it), content-addressed asset library with source, author, licence and credits.
- **Runs:** `tools/run_brain.py --section understand | lesson | director | chain` (`--fake` offline); live through `task038-live-ai.yml` modes `brain-understand`, `brain-lesson`, `brain-director`, `brain-chain` (providers = maker,reviewer; course fields in `subject`; `class_level` = earlier run URL to resume). Outputs on the `blindtest-results` branch.
- **Tests:** `tools/run_task039_tests.py`, 237 tests (48 new plus the 189 Task 038 gateway tests).

**Live runs on "10. Tissues and Its Types" (all estimated costs from the ledger)**

| Run | Maker / reviewer | Pages | Result | Cost |
| --- | --- | --- | --- | --- |
| 39610534416 | Claude Opus 5.5 (AICredits) / GPT-6.1 Sol | 3, 7 | Blocked by Anthropic: the prompt asked the model to write out its thinking for keeping and reuse ("terms … duplicating model outputs") | $0 |
| 39610917448 | Claude / GPT | 3, 7 | Strong understanding (46 items, 35 read from images), but 0 pages passed in 3 rounds: reviewer could not see the notes and failed work for precision beyond the learners' level; every remake rewrote the page | $3.59 |
| 39615516524 | Claude / GPT | 3, 7 | Patch remakes halved the second round; then AICredits stopped: "API Key Budget Exceeded" on the Claude key | $0.84 |
| 39617164262 | GPT-6.1 Sol / Gemini 4 Argon (AICredits) | 3, 7 | Both pages and the map passed (page 7, image only: 53 items) | $0.62 |
| 39620281561 | GPT / Gemini | all 14 + chain | 10 of 14 pages passed; 525 items, 1,091 teacher questions; 4 pages and the map failed only on "connection reset by peer" (fixed by streaming); lesson plan ran on an empty map (now stops instead) | $2.56 |

- **Provider terms (for Navin's later plan of an own trained model):** Anthropic's Commercial Terms forbid using the services "to build a competing product or service, including to train competing AI models", and OpenAI's Business Terms forbid using output "to develop artificial intelligence models … that compete with OpenAI's products and services". Training a BIE model on Claude or GPT outputs needs those terms checked first (or open models whose licences allow it). Process records stay useful for review and as in-context examples.
- **Open for Navin:** raise the AICredits Claude key budget if Claude should stay in the maker test; choose the video path (A or B); allow CC BY-SA assets or not.

## 21 October 2026 · what was agreed

- The whole agreement is in the Vision Spec, section "Agreed on 21 October 2026"; the build order is ROADMAP Phase 1 (Tasks 039–047).
- **Blind test verdict:** Navin rejected all three lessons as summaries ("ek summary overview lagi bas", about 5% of his expectation: prerequisites not taught, images and tables not understood, no scenes, no game). The live connections stay; the ranking is not used. Models are chosen per section by test.
- **Gold sample (draft PR #39, branch `gold-sample-tissues`):** an 8:23 video and the "Meristem Mission" game for the tissue chapter, directed by Claude by hand. Navin: visuals good but too basic, voice sounds fake, games must make learning itself the game, and it was not made by BIE. It stays a reference only, not BIE output; not to be merged without discussion. Claude force-pushed that branch once, against the rules; noted.
- **Working rule:** Claude builds BIE; content is made only by BIE.
- **Cost:** Claude's per-page estimates changed twice on 21 October and Navin does not trust them; real cost per page will be read from the ledger on the first whole run.

## Done

| Date | Task | Result |
| --- | --- | --- |
| 2026-10-19 | 036 · Scene IR producer | Canonical-complete within its bounded scope; PR #29 and #30 merged; exact-main CI green |
| 2026-10-19 | Local work rescue | Director Step 4 and Step 5 pushed as `wip/task036-director-step4` and `wip/task036-director-step5` (not merged) |
| 2026-10-19 | 037A · Repository memory | `CLAUDE.md`, Vision Spec, roadmap and this file; PR #31, merged through PR #32 |
| 2026-10-19 | 037B · Fast lane and CI debts | PR #32 merged at `d464d7f7` after all 12 checks passed on its final head `ad1436e5`. F-08 instrumented, not closed |
| 2026-10-20 | 037C · Let working source evolve | PR #34 merged at `dce749ed` after all 12 checks passed on its final head `377e313c` |
| 2026-10-22 | 039–042 · Brain frame, Sections 1–4 and 6–7 (design), asset library | PR #41 merged at `c8853eb2` after all 7 checks passed on its final head `0287f668`; Section 1 INTEGRATED, the rest IMPLEMENTED |
| 2026-10-22 | 043 · Cost guard, tarazu audit, content-type map, task-card design | PR #42 merged at `afe169b1` after all 7 checks passed on its final head `f432e245` |
| 2026-10-22 | 044 · Codex maker route, cost-guard update, private-machine kit (code only) | PR #43 merged at `9fbb256a`; IMPLEMENTED offline, the live test waits for the machine |
| 2026-10-22 | 044c · Sign in with ChatGPT feasibility report | PR #44 merged at `86a8c91d` (docs only: fast lane, no workflow ran) |
| 2026-10-22 | 045 PR A · naksha, content types in code, task cards, KI/PR/RE/PED checks, Section 2 on cards | PR #45 merged at `c08d51cb` after all 6 checks that ran passed on its head `7d8d9d2b`; IMPLEMENTED offline (fake AI) |

## Task 037B · what changed

- **Fast lane.** PRs that change only `CLAUDE.md`, `docs/roadmap/**` or `docs/vision/**` skip the three heavy gates. Every other change still runs them; they also run on each push to `main` and nightly (Post-DIR 20:30 UTC, Section 18 21:30 UTC, Section 16 22:30 UTC). A newer push to a PR cancels that PR's older run.
- **Task 036 review lock removed** (approved by Navin). `engine_identity` records hashes of the Scene IR code that actually runs; it no longer refuses to run when the 210 reviewed files change. The sealed review records stay in `docs/productization/`. The workflow-byte profile pins and their tests were removed; the dependency-version checks remain. Scene IR lane after the change: 381 of 381 tests pass on Linux.
- **M1 `verify` limit** raised from 45 to 60 minutes (it used 35m35s on exact main `b3ce527f`).
- **CI failures are now readable from here.** Each heavy job prints a bounded failure summary (failing lanes, test identities, last exception line) as run annotations, which `gh api` can read even though logs and artifacts cannot be downloaded.
- **F-08 — instrumented, not yet closed.** At least six recorded failures in at least four runs (Task 033 post-merge, D5, D7 and one more two-failure run) all show the same picture: `Page.navigate` (CDP call 7) never answered within 10 s, the operator server answered `/healthz` with 200, the browser was alive, no response for `/` arrived. Phone, tablet and desktop modes all failed, so it is not one layout. Finding: the old harness reported a closed DevTools socket with exactly the same code, so the evidence could not tell the two apart. Changes: a closed socket is now reported at once as `CDP_SOCKET_CLOSED`; the diagnostic now records whether the request was sent, whether the frame started loading, the socket state and close code, and whether the page target was still listed; the browser starts with the standard automation switches Playwright uses for this same Chromium build; the failure is published as a "Section 18 browser failure" annotation. Regression tests: `tests/section18/test_browser_journey_cdp.py` (scripted DevTools endpoint; they fail on the old harness). Local repeat run: 0 stalls in 300 fresh-profile navigations on Chromium 141 (slowest 138 ms), so the stall did not reproduce here; the new switches made no measurable difference locally (median 18 ms either way). FR-1 stays until the new evidence names the cause or the nightly runs stay clean.

## Task 037C · what changed

- **One rule** (`scripts/source_evolution.py`): working source (`bie/`, `apps/`, `tests/`, `tools/`, `scripts/`) may change through reviewed PRs; evidence (`batches/`, `historical/`, `backups/`, `docs/`, `manifests/`, `metadata/`) may not. Original archive members and recorded before-images are still checked byte for byte. A working file that differs from its adoption record is reported as evolved, not failed; a deleted working file still fails.
- **Applied to every gate-level ledger check:** `audit_canonical.py` (and its four amendment resolvers), `verify_ingested_archives.py`, `verify_post_dir.py`, `verify_section17_adoption.py`, `section16_gate.py`, the GAME adoption identity in `game_section15_gate.py`, the Task 035 provisioning guard and its CI-R1 file pins, and the post-DIR adoption test.
- **Compiler amendment chain:** its 13 sealed amendments keep proving their exact history, now against baseline copies of the 25 working files they authenticate (`docs/evidence/source-baseline-037c/`, taken from main `6fd0bdd4`, protected from line-ending conversion). Tests that build temporary roots start from those bytes (`tests/source_baseline_fixture.py`).
- **Proof:** in a copy where all 3,812 code files were changed at once, all five ledger verifiers passed (820 + 1,210 + 777 + 298 files reported as evolved), while a changed evidence file, before-image or baseline copy still fails. `tests/test_source_evolution.py` repeats this on every canonical run without writing any file.
- **Still pinned, on purpose or for later:** vendored third-party files keep their integrity checks (for example the React vendor bundle). Section 15 GAME runtime seals (`bie/game_engine/operations_engine/canonical_bindings.py` pins `bie/bie_core/artifact_contracts.py`, `bie/infrastructure/artifact_store.py` and `bie/infrastructure/idempotency_store.py`; the legacy contract seal; `scripts/verify_dsl_traceability.py`) move with Task 044. AUDIO source-identity tests (`tests/audio/test_audio_batch001_integration.py`, `tests/audio/test_audio_h1_005.py`, `bie/audio/compiler_handoff.py`) move with Task 042. Section 17 EVAL keeps one contract-blob check (`bie/evaluation/benchmarks/av/native.py`, `tests/section17/test_h2_009.py`). A few compiler M1 tests pin `bie/compiler/chromium_resource_worker.py` and its observers, and inventory checks forbid new files in `bie/qa/` and `tests/qa_*`; they are converted when a task first edits those files.

## Task 038 · live runs (20 October 2026)

- **PR #37 merged** at `398b1ace` after all checks on its final head `cc28c52c` passed. Its first CI run failed in all three canonical gates on `tests/test_source_evolution.py`: the 037C test assumed the live tree had zero evolved files, which became false the moment Task 038 evolved `schema_validation.py`. The test now compares against the tree's own evolved set.
- **Secrets set by Navin:** `OPENAI_API_KEY` (direct), `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`.
- **Probe** (run 39450001813, free): all three configured models available: `anthropic/claude-opus-5.5` and `google/gemini-4-argon` via AICredits, `gpt-6.1-sol` direct (the key also lists `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-*`).
- **Smoke** (run 39450174687): one structured call each, all valid JSON at the first attempt.
- **Blind test** (run 39450332562) on Navin's chapter "10. Tissues and Its Types" (Science and Technology, 14 pages, 11,233 characters of native text; pages 2, 7 and 8 are diagrams only and contribute no text), for UPSC / State PCS aspirants, in Hinglish. All three providers answered at the first attempt with no retries or repairs; total estimated cost about $0.36 including the AICredits markup. Outputs: `blindtest-results` branch, `runs/39450332562-blind-test/` (`REPORT.md` with letters A/B/C; `KEY.json` stays unread until Navin has chosen). The chapter PDF is on the `blindtest-inputs` branch; Navin confirmed he has permission to use it.
- Rendering fix: models that number their own section titles no longer show "1. 1." in the report.
- **Gate:** Navin scores A/B/C and picks the main model. Status words: the live connections are INTEGRATED (real upstream chapter text, real providers); nothing here is ACCEPTED.

## Task 038 · part 1

- **Live connections** behind the existing thin adapters (`ClaudeAdapter`, `GPTAdapter`, `GeminiAdapter` take a client): `bie/model_gateway/live/` adds real Anthropic (Messages API, `output_config.format` JSON schema), OpenAI (Responses API, strict JSON schema) and Gemini (`generateContent`, `responseJsonSchema`) clients on the standard library only, no vendor SDK. Keys come only from `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (GitHub Actions secrets); a provider without a key is reported as not configured, never faked. Provider error text is redacted (exact key, masked `sk-ab****xyz9` forms, key-shaped tokens).
- **`LiveGateway`:** bounded retries for timeouts, rate limits and outages (existing `retry_policy`), a content-addressed disk cache keyed by provider, model, messages, schema and prompt version, strict schema validation (new opt-in `strict=True` in `schema_validation.py`; existing callers unchanged) plus a content check, one repair turn that shows the model its error, provenance per answer, and a JSONL ledger with tokens and estimated cost for every call. Prices are estimates from public secondary sources (`pricing.py`, dated), not verified; token counts are exact.
- **AICredits route (Navin's choice, 20 Oct 2026):** Navin pays OpenAI directly and pays for Claude and Gemini through AICredits (aicredits.in, rupee wallet via UPI), an OpenAI-compatible reseller endpoint (`https://api.aicredits.in/v1`, model ids such as `anthropic/claude-opus-5.5`, `google/gemini-4-argon`; Navin keeps one key per model family: `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`). `compat_client.py` plugs into the same Claude and Gemini adapters; route rule: a direct key wins, else `AICREDITS_API_KEY`, or force with `BIE_<PROVIDER>_VIA`. Its documented JSON mode is `json_object`, so the schema also goes into the prompt and is validated locally; `no_cache` is always sent so the reseller's semantic cache never answers for the model. Ledger, provenance and `KEY.json` record the route and the model id the reseller reports; cost estimates add its 10% (5% fee + 5% forex buffer). Note: chapter text then passes through one more company (AICredits) besides Anthropic and Google; fine for textbook chapters, to be reviewed before any student data (Phase 4).
- **Deterministic fake provider** drives the real adapter → gateway → validation → ledger path offline; it proves execution, not quality.
- **Blind test** (`bie/model_gateway/live/blind_test.py`, `tools/run_blind_test.py`): chapter PDF → canonical DOCUMENT_INTELLIGENCE native text runtime → identical prompt and schema to every provider → lesson plan, narration script and exactly 5 questions → one template renders all answers → random letters A/B/C in `REPORT.md`; the letter → provider key, tokens and cost stay in `KEY.json` until Navin has chosen. Modes: `probe` (lists models each key can use, no cost), `smoke` (one tiny call each), `blind-test`.
- **CI:** `.github/workflows/task038-live-ai.yml`. Pull requests run the offline lane (188 tests incl. the 30 imported gateway contract files, a fake end-to-end blind test, canonical audit). The live lane runs only by manual dispatch from `main`; keys are given to that one step, and outputs (no keys) are pushed to the `blindtest-results` branch because artifacts cannot be read from the cloud workspace. The repository is public, so those outputs are public too.
- **037C in practice:** `bie/model_gateway/schema_validation.py` is a migrated, ledger-pinned file; `audit_canonical.py` now reports it as "evolved since adoption" and passes.
- **Next:** Navin adds the secrets (`OPENAI_API_KEY`, `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`); probe run confirms model names; smoke run; blind test on his chapter; Navin scores A/B/C and picks the main model.

## Open decisions for Navin

- [x] Approve the fast lane (037B) — yes, 19 October 2026.
- [x] Who presses merge — Claude, once CI is green (19 October 2026).
- [x] Remove the Task 036 review lock — yes, 19 October 2026.
- [x] Approve 037C (let working source evolve; evidence stays frozen) — yes, 20 October 2026.
- [x] Repository visibility — stays public (20 October 2026); CI minutes stay free.
- [x] Security timing — development speed and quality first; full security hardening before launch (planned in ROADMAP Phase 4), 20 October 2026.
- [x] Providers — Claude and Gemini through AICredits, OpenAI direct (20 October 2026); the model for each section is chosen by test on the locked chapters, quality first (21 October 2026).
- [x] First chapter — "10. Tissues and Its Types", UPSC / State PCS, Hinglish (20 October 2026).
- [x] Video form — animated, code-based (Remotion) and rendered; no AI video-generation models (21 October 2026).
- [x] Cost target — ₹50–300 per book; a cost guard now, optimisation later (22 October 2026).
- [x] Keys — never the Anthropic key; GPT API key off; only the Gemini key (AICredits) until ChatGPT Pro is connected (22 October 2026).
- [x] The Codex machine — Hostinger KVM 2, Mumbai, Ubuntu 24.04, about ₹1,300 a month, 1-month term with a 30-day refund (instead of AWS Lightsail); `bie-setup` done and the deploy key added (22 October 2026).
- [x] Task 044 Step 5 — yes (23 October 2026); done, see Task 044.
- [x] Task 045 PR B maker and checker — maker Codex (ChatGPT plan, ₹0), checker Gemini 4 Argon (another company); `gemini-3.1-pro-preview` stays off (Navin, 23 October 2026).
- [x] Task 045 PR B — the tissue chapter first (all 14 pages, map, script); Codex maker without a rupee cap (the plan's limit stops and resumes); Gemini checker cap ₹250 for the chapter; the other five chapters after Navin's verdict on this one (23 October 2026).
- [x] Seekh → BIE — standing approval, replacing the narrower "seekh → code": after every live run, use what it taught to build whatever BIE needs (code, architecture, tools, libraries, resources; move work from AI to code wherever code can do it) for Navin's quality at lower cost, without asking; tests, no earlier passed output broken, measured before and after in `docs/roadmap/SEEKH_LOG.md`; security, budget, teaching-quality verdicts and locking stay Navin's (23 October 2026; written in `CLAUDE.md` and ROADMAP).
- [x] Tissue run decisions (Navin, 23 October 2026): (1) narration 6–8 minutes per book page (this chapter about 85–110 minutes in all), a rule and a code check; a very dense page may go up to 25% over when the maker says why; must_cover stays (cut repetition and side-tracks, never book content); Section 1 and the map are not affected. (2) Prerequisites: only what this chapter directly needs, no prerequisite of a prerequisite; one short "pehle yeh jaan lo" video per chapter (5–8 minutes); a topic video has at most 1–2 reminder beats; the tissue map's prerequisites are trimmed to match. (3) A printed typo stays as printed with the right word shown: "Cartiage [Cartilage]". (4) An answer that mixes what the book says with an outside explanation becomes two answers. (5) Yes to the ~₹1 caching probe. (6) Rule CI-2 (CLAUDE.md). Brackets only on genuinely difficult words, never inside an idiom or a fixed phrase (not "आम तौर (usually) पर", not "नहीं के बराबर (equal to)"). After the fixes: rerun the tissue map trim and the script step (Gemini cap ₹150) and show v2 and the new prerequisite video.
- [ ] Task 045 PR B: Navin's verdict on the tissue chapter's map and scripts (then the other five chapters and their PDFs).
- [ ] Task 045 PR B: one chapter PDF each of History, Geography, Polity, Economics and Physics/Maths (Navin chooses the chapters).
- [ ] Optional (Task 044c): approve a one-time Sign in with ChatGPT probe on the laptop, as an exception to "never run things locally" (`docs/roadmap/SIWC_FEASIBILITY.md`, section 5).
- [ ] Optional (Task 044c): fill in OpenAI's interest form to ask whether BIE may use the plan from a rented server Navin alone controls (Claude can draft the answers).
- [ ] Optional now: a second model on the AICredits Gemini key (proposed `google/gemini-3.1-pro-preview`) — needed only for a same-company fallback when the Codex maker is unavailable.
- [ ] Monthly budget (Navin set the estimates aside on 21 October; decide on measured cost).
- [ ] Narration voice — by ear, among tested options including a cloned voice (Task 047).
- [ ] Video path: A (old Scene IR compiler) or B (brain video path, recommended) — at Task 046.
- [x] CC BY-SA assets in a paid course — no (Navin, 25 October 2026): "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi." Built as the licence gate (Task 046a-L).
- [ ] Licence gate: India Code (government terms), Hipparcos/ESA, BodyParts3D (after DBCLS answers), citation-only data (SRTM15+ and the like): approve a source by name in `bie/toolbox/licence_policy.json`, or keep it out of lessons.
- [ ] India's political boundary on maps: approve a boundary matched to the Survey of India map (until then every map that draws it stays out of lessons).
- [ ] Remotion licence: free for individuals and companies of up to 3 people; a paid company licence above that.
- [ ] What the Dhanteras goal becomes (a pilot of a few chapters?).
- [ ] Parked Director Step 4–6 work: finish, rework or drop.
- [ ] Where courses are published first.

## Known technical debts

- F-11 again (26 October 2026, Task 046 one-shot render, run 40329012680 on draft PR #76): all 15 render chunks and the
  three sample-sweep frames passed (frames kept as artifacts), but the `finish` job was cancelled at its 30-minute limit
  in its plain `apt-get install ffmpeg` step (14:23 → 14:53 UTC): the same slow regional mirror as F-11(a). Not re-run.
  Fix in the one-shot workflow: the step now uses `tools/ci_apt_prefetch.sh` (bounded downloads, one mirror fail-over),
  and a commit tagged `[render-oneshot-finish:<run id>]` joins and publishes an earlier run's frames without rendering
  them again. The toolbox lane's own apt steps still use plain apt-get (seen taking 1.5 hours on `main` the same day);
  moving them to the prefetch tool is the next small F-11 PR.
- F-13 (25 October 2026, PR #72 run 40236307455, job `demos (2)`, head `055ad618`): the toolbox `geo-relief` demo failed with
  GMT's `Remote download is currently deactivated` / `Unable to obtain remote file @earth_relief_02m_g`. Cause: a PR's
  asset cache starts empty (Actions caches made on one PR are not visible to another, and the toolbox lane does not run
  on `main`), so the SRTM15+ tiles come from GMT's data server through GMT's own downloader, which gives up after a fixed
  10-second connection limit and then switches remote data off for the session. A first fix (asking GMT again in a new
  session after 20 s and 40 s) was not enough: on PR #73's run 40238487380 all three GMT attempts failed after about
  10 s each, while the same server answered the cloud workspace in under 2 s. Not rerun (rule CI-2). Fix, in its own
  small PR (#73): `bie/toolbox/adapters/earth.prefetch_relief` fetches GMT's two server tables and the region's `.jp2`
  tiles itself (https, 120-second limit, asked again after 10 s and 20 s) into GMT's folder; GMT then converts and reads
  them offline (checked with the network blocked: the same heights, -1,422 to 7,223 m). Stale tables are fetched again
  once a day; when that fails the local ones are kept. `load_relief` still asks GMT again and names every attempt. Core
  tests with a fake server.
- F-13b (26 October 2026, PR #77 run 40319583884, job `demos (2)`, head of `task046-vm-image-look`): `geo-relief` failed
  again, this time in BIE's own fetch: `gmt_data_server.txt` timed out on all three 120-second tries (12:14:47 → 12:21:29
  UTC), then GMT's three attempts failed; the PR's cache was empty ("Cache not found"), as F-13 had named. The same server
  answered the cloud workspace in 1.8 s. Not rerun (rule CI-2). Fix, in its own small PR: the toolbox workflow gains an
  `assets` job that runs only on `main` (a push touching the downloads, weekly on Monday, and by hand) and saves the
  SRTM15+ tables and tiles (`tools/toolbox_setup.py --assets`, standard library only) as `bie-asset-cache-shared-<run>`;
  caches made on `main` can be restored by every PR, so the demo and wrapper jobs now list it in `restore-keys`. With a
  restored cache a stale table is asked for once with a 30-second limit (not three 120-second tries) and kept when the
  server is down; the tiles are already there, so GMT reads offline. The toolbox lane was also run once on `main` by
  hand to fill the per-batch caches. Core test with a fake server; the real prefetch fetched both tables and both
  tiles from the workspace.
- F-13c (26 October 2026, PR #77 run 40335061722, job `demos (2)`, head `c747dcde`, after #78 merged): `geo-relief`
  failed the same way (14:17 → 14:23 UTC, three 120-second timeouts), because the shared cache did not exist yet: the
  `assets` run on `main` (40334878992) sat in "pending" for 40 minutes behind the toolbox run started by hand on `main`
  (both in the concurrency group `bie-toolbox-refs/heads/main`; that run's apt step alone took 1.5 hours, F-11's slow
  mirror). PR #78's own run fetched the tiles at 13:31, so the server answers runners only some of the time. Not rerun
  (rule CI-2). Fix, in its own small PR: the concurrency group now includes the event, so the push-to-main `assets` job
  never waits behind a run started by hand; the `assets` job restores the last shared cache before it fetches, so once
  one run has the tiles a later outage cannot lose them.
- F-13d (27 October 2026, PR #82 run 40490842845, job `demos (2)`, head `37060f61`): `geo-relief` failed the same way
  (BIE's fetch of `gmt_data_server.txt` timed out three times, 10:58 → 11:05 UTC, then GMT's three attempts; the server
  answered the cloud workspace in 1.7 s). Not rerun (rule CI-2). **The real cause, read from the `assets` job's own log on
  `main` (run 40334878992, 26 October 14:48): the shared cache was never saved.** `actions/cache` refuses the path
  `${{ github.workspace }}/../bie-asset-cache` ("Invalid pattern … Relative pathing '.' and '..' is not allowed",
  "Cache save failed", a warning, not a failure), so F-13b's cache never existed, every PR run fetched from the one GMT
  server (`oceania`, a single IPv4 host; no other `*.generic-mapping-tools.org` data host resolves), and the next outage
  from the runners (26 October 16:44 on `main`, today on the PR) had nothing to fall back on. Fix, in its own small PR:
  the cache path is `${{ github.workspace }}/.bie-asset-cache` in all seven places (the three cache steps,
  `BIE_ASSET_CACHE` three times and `--assets`), and the core test refuses a cache path with `..`. (A first try with
  `${{ runner.temp }}` made the workflow unparseable, run 40496134303 with no jobs: the `runner` context is not allowed
  in a job's `env`; the `github` context is.) After the merge, the push-to-main `assets`
  job saves the tiles the first time the server answers a runner; from then on every PR restores them. Until that first
  save, a PR's `demos (2)` still depends on the server (PR #82 waits for it; no rerun, no empty commit).
  **Proof (27 October 2026, 12:10 UTC):** a dispatch of the toolbox workflow on the fix branch (run 40501674589) ran the
  fixed `assets` job: both GMT tables and the two SRTM15+ 2-arc-minute tiles fetched in 5 s, then
  `Cache saved with key: bie-asset-cache-shared-40501674589` (5.5 MB). A pull-request run can restore a cache made on
  its own head branch (GitHub's cache scope: the merge ref, the base branch and the head branch), so the fix PR's own
  `demos (2)` passed at 12:29 and PR #83 merged at `2146ab7d` with every check green; PR #82 brings the fix in with a
  merge from `main`.
- F-15 (27 October 2026, PR #83 run 40496661612, job `demos (3)`, head `2ba63b6e`): `hist-archive-images` failed with
  `HTTPError: HTTP Error 500: Internal Server Error` from Wikimedia Commons or Openverse (the receipt did not say which;
  the other 15 batch-3 clips passed, the five economy clips among them). Not rerun (rule CI-2). Fix, in the same small CI
  PR as F-13d: `assets._open` and `sources.fetch` ask again after a wait on a server's 500, 502, 503 and 504 as they
  already did on 429 and 503 (three tries, Retry-After honoured, 30 s at most), never on a 4xx of our own making, and the
  last error names the URL. Core tests with a fake server.
- F-16 (27 October 2026, PR #90 run 40582378287, job `demos (2)`, head `b2e2b9ec`): `astro-sky` failed with `OSError: cannot
  download https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat because <urlopen error [Errno 110] Connection timed out>`;
  14 of 15 demos passed and the PR changes only rulebook JSON, tests and docs. Cause: the shared asset cache was restored
  (`bie-asset-cache-shared-40544110585`, 5 MB) but never held the skyfield files; `adapters.astro._loader` points skyfield at
  `BIE_ASSET_CACHE/skyfield`, and skyfield's own loader downloads a missing file on the spot, so every run fetched
  `de421.bsp` (17 MB, NAIF) and `hip_main.dat` (51 MB, CDS) from the two servers; CDS timed out. CI-2: no rerun; the fix in
  its own PR (`f16-skyfield-assets`): `tools/toolbox_setup.py --assets` also prefetches both files into `cache/skyfield`
  (`prefetch_skyfield`, standard library, kept when present, an unreachable server recorded instead of raised), so the cache
  saved on main carries them for every PR; test in `tests/test_task046a_toolbox.py`. CDS stayed down for hours (both hostnames,
  from the workspace too: connection reset), so the fix PR's own `demos (2)` failed the same way: the catalogue is now also
  fetched from VizieR's mirrors when CDS does not answer (CfA Harvard answered: the same 53,316,318-byte file of 24 June 1997;
  `astro.HIPPARCOS["mirrors"]`), and the batch-2 demos job runs `tools/toolbox_setup.py --skyfield` after its cache restore, so
  a PR gets the files from a mirror and skyfield reads them from the cache folder without touching CDS. After the merge the push
  to `main` runs the `assets` job and saves the cache; then `main` is merged into PR #90 and its CI runs again.
- F-11 in the toolbox lane (26 October 2026, PR #79 run 40341502059, head `8583df52`): `wrappers` was cancelled at its
  40-minute limit inside "System libraries and programs" (14:39 → 15:18 UTC), before any test ran, and `demos (2)` sat
  in "System libraries and fonts" for over 55 minutes; `demos (1)` and `demos (3)` passed the same step in 35 seconds.
  The cause is F-11's slow regional mirror: these two steps still used plain `apt-get` with no time bound. Fix in the
  same PR (it already touches only this workflow): both steps now download through `tools/ci_apt_prefetch.sh` (one
  480 s budget, mirror fail-over, an `::error` annotation instead of a silent cancel) and install from the local
  cache. Not rerun; the push that adds this note starts the new run (rule CI-2).
- F-14 (26 October 2026, VM runner): the first job after PR #77 merged (`codex-jobs:jobs/t046-oneshot-images.json`)
  came back `refused: unknown fields: max_images, prompts`. Cause: `tools/codex_vm.py poll` imports the runner, then
  moves the checkout to the new `main`, then checks the jobs with the rules it had already loaded, so the first poll
  after any runner change runs the old code (and a refused id is never run again). Fix, in its own small PR: a poll
  that moved the checkout starts itself again once (`BIE_VM_FRESH=1`) with the new code, after releasing its lock.
  The job was resubmitted as `t046-oneshot-images-2`. The same PR adds `tests/test_task046_vm_image.py` (PR #77's
  runner tests, which no lane ran) to the Task 044 lane and its paths. The resubmitted job ran (1.8 minutes, plan usage
  0 % before and after, ₹0) but made no image: all four `codex exec` runs completed with an `error` item and a reply and
  no image item, and BIE did not keep either text. The same PR keeps them: a run without an image now fails with
  Codex's last error and its reply (redacted like every Codex failure), so the next job names the cause. Likely cause,
  from Codex's documentation and guides: image_gen is reached through Codex's built-in `imagegen` skill (headless:
  `codex exec '$imagegen ...'`), and BIE's image call kept the lean call's skill settings and did not name the skill.
  Image calls now keep skills on and start with `$imagegen`; shell, exec, code mode, apps, browsing and agents stay
  off and no API key reaches Codex. Google fallback checked: Google's pricing page lists no free tier for any image
  model (a call to `gemini-2.5-flash-image` with the free key returned 429, run 40376215362), and the AICredits key
  may call only `gemini-4-argon`, so neither Google route can make the Route 2 images without Navin's decision.
- F-14b (26 October 2026, VM job `t046-oneshot-images-3`, after PR #80): the kept error named the cause. All four runs:
  "Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable
  `features.code_mode_host` and install `codex-code-mode-host`", then the reply "DONE" with no image (1.4 minutes, plan
  usage 0 %, ₹0). In Codex 0.162.1 every tool call goes through the code-mode host that ships beside the codex
  binary, and BIE's lean settings turn it off. Fix (it touches the isolation boundary on his machine; **Navin said yes
  on 26 October 2026**, “option 1”): image calls keep `code_mode_host` on; shell, unified exec, apps, plugins, browsing,
  computer use and agents stay off, the run stays read-only in an empty folder, and no API key reaches Codex.
- F-11 (native-render flakiness, seekh → BIE work, its own small PR): (a) PR #48 run 39890973906: the job was cancelled at its 20-minute limit while provisioning, before any test ran, and was rerun once; that rerun happened before rule CI-2 existed. (b) PR #53 run 39934589208 (head `332d2c31`): the render lane's `NativePreviewRender.setUpClass` failed closed with `CHROMIUM_RESOURCE_FAILED:CHROMIUM_RESOURCE_MONITOR_NOT_FROZEN` (`bie/compiler/chromium_resource_worker.py` saw the cgroup not frozen when capturing a member), process not started; the same job passed on `main` at `e0241cd0` minutes earlier and the PR touches no compiler code. Not rerun (rule CI-2: the failure came after tests started). (c) PR #53 run 39986108672 (head `4dc8db7d`): cancelled at the 20-minute job limit in "Provision unchanged governed native toolchain", before any test ran. Cause from the job log: apt-get downloads from `azure.archive.ubuntu.com` (noble/universe media libraries) were very slow, for example `libflite1` (13.6 MB) took 4 minutes (16:37:36 → 16:41:36), and the step has no time bound of its own. The same cause as (a). Rerun once under rule CI-2 (the push that adds this note starts the new run); the real fix (bounded apt retries and timeouts, or fewer packages) comes in the F-11 PR.
- F-12 (24 October 2026, PR #62 run 40109667708, head `b3d301d3`): the Section 18 independent browser gate failed on the tablet journey of batch002 with `BROWSER_START_FAILED` and an empty diagnostic, 44 seconds after the step started (the phone journey before it passed), so not after the 30 s start budget. Cause, from the harness: `browser_journey.mjs` stopped polling `/json/list` at the first answer and asserted the list was not empty; Chromium's DevTools HTTP endpoint can answer before its first tab is registered, so an empty list made the gate fail at once. Not an FR-1 code, so no rerun (rule CI-2): fixed in its own small PR: the harness keeps polling until a page target is listed, within the same 30 s, and a real failure now reports how many polls were made, whether the endpoint answered and how many targets it listed (`startPolls`, `startAnswered`, `startTargets` in the "Section 18 browser failure" annotation). Regression tests with the scripted DevTools endpoint: an empty first list passes the start stage; no target in 30 s fails with that evidence. The PR touches no code the diff of #62 touches.
- F-08: Section 18 browser gate flake (`CDP_TIMEOUT:Page.navigate`); instrumented in 037B, cause not yet proven. FR-1 allows one recorded rerun per job only for that exact failure (or `CDP_SOCKET_CLOSED:Page.navigate`).
- F-11 fix (PR #55, merged at `cb198dff` on 23 October 2026 after all 16 checks passed; it touches the isolation boundary and Navin said yes; on the PR's own run native-render provisioned and passed in 4 minutes): (b) root cause: in cgroup v2 a member that is counted frozen and then takes a fatal signal (a kill sent before the re-freeze, or a pid-namespace zap or parent-death signal after another member's exit) leaves the frozen count until it exits (`get_signal` fatal path, `cgroup_leave_frozen(true)`), so `cgroup.events` reads `frozen 0` while `cgroup.freeze` is still 1; reproduced on a real cgroup v2 leaf (old code `MONITOR_NOT_FROZEN` 8 of 550 trials, fixed code 0 of 530). Fix: `capture_frozen_member` waits at most 2 s for the kernel to report frozen again, only while BIE's own freeze request is in force; the same `frozen == 1` check and every identity check still decide. (a) root cause: `.deb` downloads from the runner's regional mirror `azure.archive.ubuntu.com` crawled at 45–104 kB/s (healthy: 95 MB in 5 s) and apt has no minimum speed; fix: `tools/ci_apt_prefetch.sh` downloads the same packages first under one 480 s budget (first try 180 s), fails over once to the runner image's next listed mirror and then installs from the local cache, with an `::error` annotation instead of a silent cancel; apt still verifies every package against the signed indexes. The 20-minute job limit stays.
- npm drift (found and fixed in 037B): from 17 October the Section 18 `native-render` job failed on every PR, docs-only #31 included, with `TOOLCHAIN_REMOTION_PAIR: mixed versions`. Cause, shown by the drift canary: the generated Remotion project has no lockfile, a newer webpack now gets hoisted, and npm nests Remotion's exact `webpack@5.105.0` under `node_modules/@remotion/bundler/`; the pairing check counts every entry under that prefix, including this non-Remotion package. 037B resolves those installs, and the M1 render runner's, as of 17 Oct 2026 12:00 UTC (`tools/npm_before.txt`); native-render is green again and the canary keeps reporting today's unpinned tree. Follow-up: commit a real lockfile and narrow the check to Remotion packages (possible now that 037C allows the edit).
- F-09 (seen once, passed on the next full run): Section 18 atomic `CancelRecovery.test_actual_two_process_cancel_returns_same_completed_state` failed in PR #32 run 39292713985 (both child processes exited 1). It passed on PR #31's run and 90 of 90 times locally (30 of them under full CPU load). Suspected: SQLite's 1 s busy timeout while two processes prepare the same cancel on a slow runner, so one child gets "database is locked" and the other times out at the test's 8 s barrier. Not proven; failure annotations now include the children's stderr.
- F-10 (seen once, passed on the next full run): `tests/compiler/test_comp_render_integration.py` errored once in the canonical gate of PR #34 run 39362113041. Nothing under `bie/compiler/` or `tests/compiler/` changed between that run and the previous green run of the same PR. The file contains a 0.8-second process-start timeout (`test_process_group_timeout_stops_descendant`), the likely cause on a busy runner. Not proven; canonical-gate annotations now include each failing test's exception line.
- N-02: Section 18 source-ledger step slowed from 21 s to 612 s.
- Audio reconciliation open (`AUDIO_REPLAN_REQUIRED`); global VIDEO_CODE and later stages not run.
- PR29 follow-ups F-01..F-07 and PR30 follow-ups F1..F5 (low, non-blocking).
