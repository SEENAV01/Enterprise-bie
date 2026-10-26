# BIE Roadmap

Living plan from 19 October 2026. The why is in `docs/vision/VISION_SPEC.md`; the current task is in
`docs/roadmap/STATUS.md`.

Task numbers from 037 onward follow this roadmap. ChatGPT's earlier proposal for Tasks 037–060 is retired;
its mapping onto these phases is kept in the Vision Spec. Durations are estimates and are re-estimated at every
gate.

## How every task runs

1. **Task card** — a short Hinglish card for Navin: what will be built, what he will see, how we know it is done.
2. **Navin says "haan"** (or asks for a change).
3. **Build** — branch `task0NN-<slug>` from current `main`; code and tests run on Linux in the cloud workspace.
4. **Show the output** — the real thing (a script, a video, a game, a report), not only test counts.
5. **PR → CI → merge** — Claude merges once every check is green (Navin approved this on 19 October 2026).
6. **Update `docs/roadmap/STATUS.md`** and show the next task card.

## Phase 0 · Foundation (about 2–3 days)

**037A · Repository memory** — `CLAUDE.md`, Vision Spec, this roadmap and the status file in the repo.
Docs only; no code changes. Done when merged.

**037B · Fast lane and CI debts** — approved by Navin on 19 October 2026.
- Before: every PR to `main` ran three all-path heavy workflows (Post-DIR canonical about 45 min, Section 16 QA combined, Section 18 about 42 min) plus the matching producer workflows, even for a documentation change.
- Fast lane: changes only to `CLAUDE.md`, `docs/roadmap/**` and `docs/vision/**` skip the three heavy gates; every other change still runs all of them; they also run on every push to `main` and nightly. No gate is weakened, deleted or made non-blocking for code it covers.
- Remove the Task 036 runtime review lock (approved by Navin): Scene IR records hashes of the code that actually runs instead of refusing to run when reviewed bytes change.
- F-08 (Section 18 browser `CDP_TIMEOUT:Page.navigate` before the first product assertion): find the cause, add a regression test and remove the rerun rule FR-1 once it is closed.
- M1 `verify` took 35m35s of its 45 min limit; raise the limit to 60 min on that timing evidence.

**037C · Let working source evolve** — approved by Navin on 20 October 2026.
- `scripts/audit_canonical.py` byte-pins every migrated source file listed in `manifests/lossless_migration.csv`, including `bie/model_gateway/`, `bie/knowledge_intelligence/`, `bie/prerequisite_intelligence/` and `bie/reasoning/`; `scripts/verify_post_dir.py` does the same for adopted VISUAL/ANIMATION/DSL/COMPILER files. Tasks 038–041 must edit these files.
- Proposal: keep the original bytes checked inside the archived ZIPs (provenance stays provable) and keep `batches/`, `historical/`, `backups/` and `docs/evidence/` byte-frozen, but let working source under `bie/`, `apps/` and `tests/` change through normal reviewed PRs, with one evolution register instead of a new amendment module per change.
- Done when: a deliberate edit to a pinned `bie/model_gateway/` file passes the canonical gate, and an edit to frozen evidence still fails it.

**038 · Live AI and the blind test**
- Real provider adapters (Claude, OpenAI, Gemini) behind the existing `bie/model_gateway/` interface; keys only from environment or GitHub Actions secrets, never in the repo or chat.
- Structured output with schema validation, bounded retries, response caching, and token and cost logging per call.
- A deterministic fake provider keeps every existing test offline and repeatable.
- Blind-test harness: one real chapter → lesson plan, narration script and 5 questions per provider → anonymised A/B/C report for Navin.
- Result (21 October 2026): the connections work, but Navin rejected the blind-test lessons as summaries
  ("ek summary overview lagi bas"), so its ranking is not used. Models are chosen per section by test
  instead (see the Vision Spec, "Agreed on 21 October 2026").

## Phase 1 · BIE as one whole system on the tissue chapter

Agreed with Navin on 21 October 2026 (Vision Spec, "Agreed on 21 October 2026"). BIE is built section by
section in the order a chapter flows through it. Every section does its full job from the start; Claude tests
each one internally, and Navin judges only the whole package that one run produces. Test chapter: "10. Tissues
and Its Types" (Science and Technology, UPSC / State PCS, Hinglish).

**039 · The brain frame and understanding the book**
- Vision rulebook inside BIE: Navin's vision as versioned rules and checklists that every section and the
  reviewer load.
- One section runner: instructions and source (text and page images) → the AI writes its thinking and its
  output → code checks → reviewer AI from another provider → bounded remake → full process record and ledger.
- Section 1: two-eye reading, item inventory with locations, question-based understanding, content types,
  prerequisites, PYQ links, chapter map and coverage. Replaces the regex knowledge scan.

**040 · Lesson plan and teacher script** — videos per chapter, order, prerequisites taught first, Hinglish
spoken script in beats, stories and analogies only where they fit, length from content.

**041 · Director** — the universal question frame, visual mathematics and subject styles; scene descriptions
for every beat.

**042 · Visual library and animation blocks** — biology first: 3D models, detailed SVG and illustrations with
licences, a fast online asset fetch, AI images only for gaps; blocks written by AI, compiled to Remotion code,
locked after review.

Tasks 039–042 were built together and merged in PR #41 (22 October 2026). The old entries 043 Voice,
044 Render, 045 Game, 046 Notes and 047 Review are superseded by the plan agreed on 22 October below: Voice is
now 047, Render 048, Game 049, Notes 050, Review 051–052.

### Agreed on 22 October 2026: BIE is the system between Navin and AI (binding)

BIE must (1) understand the whole book as a chapter map; (2) tell the AI exactly what to make, through compact
task cards and fixed output formats (`docs/roadmap/TASK_CARD.md`); (3) check every AI output with code and a
second AI; (4) build video, game and notes with its own engines, the AI only filling data; (5) record and lock
whatever passes, so it gets more exact with every book. It is not a prompt wrapper. Lesson content is made only
by BIE, never by hand.

**The tarazu (five points).** Every section must meet: 1 understanding, 2 teaching and video, 3 game, 4 notes,
5 review and lock. The audit of every old section and brain module, with its gap, decision (use, extend, or
replace and retire) and fixing task, is `docs/roadmap/TARAZU.md`.

**Order.**
1. Make every section meet the five points, merging the brain code into the old BIE code: one BIE, no parallel
   systems. For each old engine: use it, extend it, or replace it and retire the old one explicitly.
2. Connect ChatGPT Pro early (Codex, on a private machine).
3. After each section: run it on the tissue chapter plus 4–5 chapters from other subjects; Navin judges.
4. Wire everything into a one-button software.
5. Only then: decide the heavy or light method, optimise cost, and later train BIE's own model.

**Seekh → BIE (standing approval, Navin, 23 October 2026; replaces the narrower "seekh → code").** After every live
run, what the run taught is used to build whatever BIE needs to make what Navin wants at the quality he wants, and to
make it cheaper: any code, architecture, tools, libraries or resources. Build what is missing, improve what exists, and
move work from AI to code wherever code can do it; code checks for repeated reviewer findings are one part of this, not
the whole. Claude does it without asking. Every change has tests, must not break outputs that passed before, and is
measured before and after (quality, first-try pass rate, rounds, tokens, ₹ per page) in `docs/roadmap/SEEKH_LOG.md`.
Still Navin's: security-sensitive changes, budget, teaching-quality verdicts and locking accepted examples.

**Cost.** Target ₹50–300 per book. Optimisation comes later, but the cost guard is in place from Task 043:
estimate before a run, preflight, hard cap (`max_inr`, default 300), rupees per section and per page after.

**Keys.** Never use the Anthropic key. The GPT API key is off. Only the Gemini key (AICredits) until ChatGPT
Pro is connected. Nothing runs on Navin's laptop; heavy work runs in GitHub Actions.

**043 · Cost guard, tarazu audit, content-type map, task-card design** (this plan)
- Cost guard ("pahra"): preflight call per route; estimate "Andaaza ₹X, seema ₹Y"; hard cap; rupees per
  section and per page in SUMMARY.json; a slot for the real dashboard bill (`docs/roadmap/COST_LOG.md`).
- `docs/roadmap/TARAZU.md`; `bie/brain/rulebook/content_types.json`; `docs/roadmap/TASK_CARD.md` with its
  JSON schema.
- Research: batch mode and prompt caching on AICredits and Gemini; the Gemini models on the key; a maker and a
  different checker model (same company, temporary, marked in records).

**044 · ChatGPT Pro engine** — Codex as a maker route on a private machine. First check whether Navin's
JioPC (an Ubuntu cloud PC that shuts down 15 minutes after disconnect) can host it; otherwise a small cloud VM,
with its monthly cost shown to Navin before anything is bought. The Gemini API stays as the checker. Done when a
brain section runs with Codex as maker and Gemini as checker, under the cost guard, recorded like any route.
Decided on 22 October 2026 (`deployment/codex-vm/README.md`): Codex cloud works only as a slow hand-off and JioPC
shuts down, so the maker runs with `codex exec` on a small private machine (recommended AWS Lightsail Mumbai,
about ₹1,340 a month), never in this public repository's Actions. The route, the cost-guard update and the
machine kit are built first; the live test runs once Navin has said yes and signed the machine in.
Machine (22 October 2026): Navin chose Hostinger KVM 2 in Mumbai (Ubuntu 24.04, about ₹1,300 a month, 1-month term,
30-day refund) instead of Lightsail and finished `bie-setup`; the Step 5 live test (tissue pages 1, 7, 11, 13, cap ₹30)
runs after his yes to its estimate. Done 23 October 2026: all 4 pages passed with the Codex maker (Gemini ₹23.55, plan
0% → 1%); the map check was stopped by the cap.
Task 044c (22 October 2026, report only, `docs/roadmap/SIWC_FEASIBILITY.md`): the Codex route stays primary;
Sign in with ChatGPT is an optional later route, only after a one-time probe (needs Navin's yes) and an answer
from OpenAI on where tokens may be stored.

**045 · Understanding and script on the tarazu** — a compact chapter map shared by all sections; content-type
detection in code (`content_types.json`) compared with the AI's type; task cards for Sections 1 and 2; merge
with the old KI, PR, RE and PED engines as code checks (TARAZU rows). Run: tissue + 4–5 chapters of other
subjects; Navin judges.
PR A (22 October 2026, branch `task045-understanding-script`): the naksha (`bie/brain/naksha.py`), type detection
(`bie/brain/content_types.py`), task cards (`bie/brain/cards.py`), the KI, PR, RE and PED engines as checks
(`bie/brain/engines.py`) and Section 2 on the card, tested offline with the fake AI. PR B: the live runs, only after
Navin's yes to the estimate, the checker choice and the five chapter PDFs.
PR B, Navin's decision (23 October 2026): the tissue chapter first, all 14 pages, the chapter map and the script; maker
Codex (ChatGPT plan, no rupee cap; the plan's own limit stops a run, which is resumable), checker Gemini 4 Argon with a
₹250 cap for the whole chapter. The other five chapters wait until Navin has judged this one.

Tissue run decisions (Navin, 23 October 2026), built as seekh → BIE before the map trim and the script run again (Gemini cap ₹150): narration 6–8 minutes per book page (up to 25% over for a dense page with the reason stated; must_cover stays); only direct prerequisites, taught in one 5–8 minute "pehle yeh jaan lo" video per chapter, at most 1–2 reminder beats in a topic video; printed typos kept with the right word shown; mixed book/outside answers split in two; brackets only on genuinely difficult words and never inside an idiom; the caching probe; CI rule CI-2.

Task 045d · teaching soul (Navin, 24 October 2026; `docs/vision/TEACHING_SOUL.md`): the tissue scripts restated the book, so
every book line is now opened, for every subject: Section 1 writes an `unpack` per teachable item (terms with their plain meaning
and an everyday image, a why chain from a need with its basis, an example or place, a consequence; rule S1-15); level profiles
(`level_profiles.json`: school, neet_11_12, upsc_pcs, revision) chosen from the course setting and the book's own text, a
disagreement stops the run for Navin; flexible pattern steps with a stated reason and a family pattern for a classification;
the script opens every line (question first, yaani with an image, a why or an example; complete sentences; one recap per part;
rule S2-07) with the code checks "dohraav pakad" and the `dohraav` measure; the teacher example bank
(`teacher_examples.json`) in every prefix; the explanation library (`explanations.json`) locked only by Navin's verdict; rules
G-06 and G-07 (BIE is the link; two layers). Run after merge: the tissue understanding and script again (maker Codex, Gemini
checker cap ₹200), old v2 against new v2 and the dohraav number before and after; nothing ACCEPTED until Navin's verdict.

Navin's verdict (25 October 2026): he read old v2 (epithelial, `vm-t045c-tissue-lesson-v9`) against the new epithelial script
(new v3, `vm-t045d-tissue-lesson-resume2`; the new plan splits videos differently, so topics are compared by topic, not by video
id) and chose to **go forward with the NEW scripts. Task 045 is complete for now.** 045e (completeness and full sentences) is not
done now: if, after the one-button software (051), a real book's output shows a gap in any section (teaching, video, narration,
notes), Navin opens a new improvement task then. The reviewer stays a permanent part of BIE; from 25 October 2026 it runs on
Navin's free Google AI Studio key on the VM (`gemini-3.8-flash`, direct route; sample content only, never student data). His
observations, for the record only: the new scripts use more examples and analogies; the old ones had fuller sentences and more
completeness; some new sentences feel clipped. The next task (046a, the tool house) starts only after Navin says so.

**046a · Auzaar-ghar (toolbox)** — started 25 October 2026 on Navin's brief, cost ₹0 (no AI calls), three PRs. Every library,
tool and asset source BIE may need to show what a scene plan asks for is joined into BIE, wired and proven: `bie/toolbox/`
holds the registry (`registry.json` + schema + loader: kind, subjects, content types, capabilities, role, render path, pinned
version, licence with share-alike/GPL/custom flags, source, install group, status from installed to used_on_real_book, proof),
the fixed capability vocabulary (`capabilities.json`: Navin's 41 capabilities plus `split_compare` from the benchmark, tied to
the content types and the 045d visual verbs) and a resolver (capability, subject, level, path → the tools that draw, compute and
supply assets, with a fallback path; a capability nothing provides is logged as "missing" for seekh → BIE and the 046 merge
path). Two render paths, one bridge: the web path (BIE blocks for Remotion, previewed by remotion-lite, with three.js through
@remotion/three, React Three Fiber and drei; KaTeX, D3, 3Dmol.js, Mol*, matter.js, cannon-es) and the Python/offline path
(compute libraries return JSON; Blender headless exports glTF for route C; Manim renders clips). Large files are fetched on
demand into the asset cache with licence and credit, never into git. Every tool is proven by a 3–5 s silent demo clip made by
BIE code (with a contact sheet) or by a test; the status words are claims the demos lane checks on every run. Batch 1: core +
biology, chemistry, maths, physics, computer science; batch 2: electrical, mechanical/civil, earth, astronomy, aerospace;
batch 3: geography/history/polity, economics, law, psychology/education/sociology, languages, and the UGC NET / GATE
mapping (`bie/toolbox/exam_map.json`: the official lists of 25 October 2026 have 86 UGC NET subjects plus Paper I, not 84, and
30 GATE papers). After each batch Navin sees the toolbox page (`docs/toolbox/TOOLBOX.md`), the clips, what is blocked and why, and the
missing capabilities. Batches 1–3 merged (PR #69, #70, #71). Repo visibility stays Navin's decision.

**046a-L · Licence gate** — Navin's decision, 25 October 2026, in his words: "Final videos mein sirf CC0 aur CC BY assets
lein; CC BY-SA nahi; NC bilkul nahi." One PR, cost ₹0. One policy file, `bie/toolbox/licence_policy.json` (versioned and
dated, his words in it), is the only source of truth; every licence decision (the asset library, the toolbox sources, the
registry checks, the resolver, the toolbox page) reads it through `bie/toolbox/licence.py`, and no verdict is written per
tool by hand. Lesson content (anything seen or heard in a lesson video, game or notes): allowed = CC0, public domain (the
Public Domain Mark, US government works stated as public domain) and CC BY of any version with author, licence, licence URL
and source page; refused = CC BY-SA and every share-alike licence, any NC, any ND, a missing or unreadable licence; needs
Navin = own terms (India Code, Hipparcos/ESA, BodyParts3D, citation-only data such as SRTM15+, anything the registry marks
custom), blocked until he approves the source by name in the file; per item = NASA, Commons, Openverse, NIH 3D, PubChem,
Sketchfab-type sources, checked file by file (a NASA file with third-party rights is refused). India's political boundary
(any map or asset that draws it, Natural Earth's India view included) needs Navin until he approves a boundary matched to
the Survey of India map. Software is not content: a program's licence governs the program, not what BIE draws with it;
GPL-family programs run only in the cloud, CI or VM and never ship inside `apps/` (a test fails otherwise); data a tool ships
with is content. The gate (`lesson_licence_check`) runs before any lesson output is rendered or packaged — the visual section
(before layout and before a VideoSpec is written), the game builder, the Scene IR asset resolution, the compiler's asset
bundle, and `AssetLibrary.require_lesson`, the hook the 046 director calls — and stops that output with the reason; nothing
is swapped silently; every passing output gets a credits list from the asset fields. The share-alike switch is gone. The
resolver lists sources a lesson may not use as "not for lessons" and logs a capability left without an allowed source as
missing, for seekh → BIE. Proof clips with refused or needs-Navin content stay as evidence, marked "internal proof, not for
lessons" (9 of 51). IMPLEMENTED; not used on a real book yet. Still Navin's: India Code, Hipparcos/ESA, BodyParts3D,
citation-only data, India's boundary, and the Remotion licence (free for individuals and companies of up to 3 people, paid
above that). Task 046 starts only after Navin says so.

**046 · Director, video blocks and the benchmark video** — the presentation layer, built to the benchmark
(`bie/brain/rulebook/benchmarks/epithelium_animation.json`, rule S3-06): one spoken sentence is one shot of 2–4 s; about
40–50 s per family member; said = shown, a function sentence shows motion; a term opened with "yaani" on first use and every
name given its reason; one "A → B" summary line per member on a board that fills; the spoken words on top with the English
terms coloured; "where found" by a zoom from the organ; a focus glow; one dark style; the depth of what is shown follows the
level profile, the visual grammar follows the benchmark. The presentation is the same skilled quality for every learner (G-07).
- **Blocks** (code, tested, reused): `cell_sheet`, `particle_flow`, `organ_zoom`, `focus_glow`, `kinetic_caption`,
  `concept_arrow`, `board_build`, `mnemonic_card`; planned next: `tree`, `split_compare`, `cause_chain`. The director maps every
  script sentence to one shot and one block, with the beat's `visual_verb` from the unpack.
- **Two render routes, both code, no AI video model.** Route A: three.js scenes rendered through Remotion (the Scene IR and the
  COMP compiler of Sections 13–16 extended, not replaced). Route C: 3D models made once, by Blender Python scripts or from
  licensed models in the asset library (licence and credit recorded), animated by BIE code; the same block API renders through
  either route. The asset finder v2 (library first, then Wikimedia Commons and Openverse, SVG preferred, a vision AI chooses, an
  AI-drawn SVG last) feeds route A's flat assets and route C's textures.
- **Head to head:** BIE's own engine against AI-written block code on the same benchmark, judged by Navin on the same
  sentences. **Merge path:** an AI writes a block's code once, BIE tests it (frame checks, the said = shown check, the licence
  check), Navin approves it, and the block joins the library and is reused for every later book.
- One scene format decision (Scene IR vs VideoSpec, Navin's video path). Output: silent videos of the tissue chapter rendered
  through both routes on the benchmark's shots, judged against the benchmark shot by shot. Navin judges.

**Navin's decisions, 26 October 2026 (Task 046 brief), in his words:**
- "Task 46 will surpass even the tarazu point 'video kaisi ho' level on its full completion, implementing things required."
- Chain: content decides the scene plan; the scene plan decides which visual level the video code is made at. BIE itself must
  be capable up to L5a. "90 se 99 percent videos L3 ya isse upar ke level ki ho."
- Verdict of 25 October: present the book's knowledge with completeness, teacher style, examples and analogies, "like a truly
  class animated video" (the epithelium benchmark). Video length stays open, driven by completeness.
- Narration never says "book के अनुसार", "किताब कहती है", "book says" or any wording that points at the book. BIE teaches as a
  teacher; Navin accepts the copyright position.
- Lesson assets: only CC0, public domain and CC BY (the 046a-L gate). Reference videos are for calibration only; no frame,
  footage, logo or text from them enters the repo (the repo is public).

**The visual level ladder** (`docs/vision/VISUAL_LEVELS.md`, `bie/brain/rulebook/visual_levels.json`): L1 teacher at a board
(never a BIE target), L2 clean 2D, L3 rich 2D/2.5D, L4 stylized 3D (one world per topic, cutaway, exploded view, flow), L5a
photoreal micro or machine 3D (the benchmark level), L5b photoreal humans and Pixar-grade acting (outside BIE's output; a plan
that asks for it fails). Every shot carries `level` ∈ {L2, L3, L4, L5a}; a capability's default level lives in
`capabilities.json`; per video, shot seconds at L3 or above ≥ 90 %, else not rendered.

**The visual grammar** (`bie/brain/rulebook/visual_grammar.json`, VG-01…VG-11 on top of the benchmark's B-01…B-12): one topic
one 3D world with the camera moving between parts; labels as code text with leader lines; inside by cutaway or exploded view;
size by scale comparison; equations step by step beside the picture; self-drawing graphs; split screen for comparison; flow for
processes; one dark background, one accent per concept, one camera language; a lit timeline for history and polity, maps only
through the licence gate's map rule; a 2D guide character only where topic and level ask. Plus **W-01**, the wording rule, as
a soul.py check with the word list in the rulebook.

**Three PRs.** Part A (the code director: ladder, grammar, W-01, capability levels and blocks, `bie/brain/shots.py`, the
offline proof on v3, VM job 1 = the W-01 wording patch on v3 at ₹0) — done 26 October 2026, IMPLEMENTED (STATUS, "Task 046 ·
Part A"). Part B (blocks as code with frame checks and demo clips, route A three.js through Remotion and route C procedural or
Blender models, espeak placeholder voice or silent captions, the epithelium family segment of v3 rendered in CI, cost table,
24-rule table shot by shot, a ≤ 720p review copy on `blindtest-results` and an artifact page) — then stop for Navin's verdict.
Part C after the verdict (fixes, all of v3, the head-to-head VM job 2, seekh → BIE). Status words: IMPLEMENTED until Navin
says ACCEPTED.

**047 · Voice** — extend Section 14: tested natural voices including a cloned voice (Navin chooses by ear);
word timestamps drive the animation; close the AUDIO reconciliation.

**048 · Render and interactive player** — real Remotion render through the COMP compiler in the cloud, frame
checks (Section 16 video QA and a reviewer AI); the same code as an interactive player (pause questions,
tap-to-explore).

**049 · Game** — the Section 15 decision (one engine), the builder, the bot playtest on a phone screen, and the
book world that joins chapter games as levels.

**050 · Notes** — the full summariser design: question-based slides in three depths, "kitaab mein nahi bataya
gaya", source pages, "book says" separate from "latest update" (link and date checked), code-drawn
infographics, slides and PDF; an engine the summariser app can reuse.

**051 · One-button software and review page** — extend the Section 18 operator app: upload a book, run every
section under the cost guard, then watch, play, read and give a verdict in Navin's words; fail comments become
rules Navin approves; passes lock examples with their process records.

**052 · Real test** — the tissue chapter plus one chapter per content type, end to end; Navin decides the heavy
or light method; then cost optimisation (batch, caching, locked blocks) and, later, BIE's own model.

**Gate 1:** one BIE run turns the tissue chapter into video, game and notes; Navin judges the whole package;
the real cost per page is read from the ledger and compared with the dashboard bill.

## Phase 2 · Every kind of subject

- Chapters from other subject families (history, mathematics, geography, law and more), then full UGC NET
  books: Navin and the reviewer AI review, rules lock, libraries grow per subject; real cost and time per page
  measured from the ledger.
- Model choice per section by test on the locked chapters.
- Navin's "gold lessons" are BIE outputs he passed; story mode for suitable topics.
- Bigger building-block library; the asset intelligence layer (Wikimedia Commons and other open sources, licence tracking, SVG part tagging, restyling, cache).
- Auto-repair of failed renders and QA; quality benchmark.
- One full ~300-page book end to end.
- **Gate 2:** students prefer a BIE lesson to a normal class.

## Phase 3 · Course factory

- Course assembly (book → modules → chapters → lessons → videos → quizzes → revision) and multi-book reconciliation.
- Six languages: English, Hindi, Hinglish, Tamil, Marathi, Spanish.
- Reuse memory: retrieve and adapt proven lessons, scenes and blocks.
- Admin dashboard (extend the Section 18 operator app); batch scheduler, parallel cloud workers, checkpoint and resume, cost dashboard.
- **Gate 3:** 4–5 books of ~300 pages processed in one day.

## Phase 4 · Launch

- Publish to the learner app; family subscription with per-profile access and device-based pricing.
- Security, tenancy, secrets, deployment and final acceptance.
- **Security hardening before launch** (Navin's decision, 20 October 2026: development speed and quality first, full security once the product is ready):
  - Review repository visibility (public now for free CI); move to private if the code or plans need protecting.
  - GitHub branch protection with required checks, so nothing reaches `main` without green CI.
  - Signed release manifests: every shipped file fingerprinted, and the deployed build verified against it (the right kind of anti-tamper seal).
  - Classify the remaining Section 15 GAME, AUDIO and EVAL runtime seals: keep real protections (sandbox, vendored-library integrity), turn freeze-only checks into recorded provenance.
  - Keep the BIE engine server-side; protect learner-facing content with account-based access and licence terms; secrets audit.
- Then the public self-serve tool.
