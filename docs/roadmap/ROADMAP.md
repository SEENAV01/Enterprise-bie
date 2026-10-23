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

**046 · Director, asset finder v2 and silent video** — the director's scene plan drives the asset finder:
the library first, then Wikimedia Commons and Openverse; SVG preferred; part locations read from SVG text;
choice by a vision AI; an AI-drawn SVG as the last fallback; adapt the asset to the scene; add it to the
library with licence and credit. One scene format decision (Scene IR vs VideoSpec, Navin's video path).
Output: silent videos. Run on the chapters; Navin judges.

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
