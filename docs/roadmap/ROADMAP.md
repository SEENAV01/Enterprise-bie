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

**043 · Voice** — tested voice options including a cloned voice (Navin chooses by ear); word timings drive the
animation; resolve the open AUDIO reconciliation.

**044 · Render and interactive player** — VIDEO_CODE → compile → render in the cloud → frame checks by a
reviewer AI; the same code as an interactive player with questions and tap-to-explore.

**045 · Chapter game** — game designer AI on the Section 15 engine; missions from content types; item →
mission coverage; bot playtest on a phone screen.

**046 · Notes** — Navin's summariser design: question-based infographic slides with three depths, source
links, "book says" and "new now", and a PDF; built as an engine the summariser app can reuse.

**047 · Review page, rulebook and test set** — Navin's review page (watch, play, read, pass or fail with his
words); fail comments become rules he approves; passes lock examples and process records; the test set reruns
on every change of code, rule or model.

**Gate 1:** one BIE run turns the tissue chapter into video, game and notes; Navin judges the whole package;
the real cost per page is read from the ledger.

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
