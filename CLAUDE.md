# CLAUDE.md — Book Intelligence Engine (BIE)

Read this file first, then:

1. `docs/roadmap/STATUS.md` — where we are right now and the current task.
2. `docs/vision/VISION_SPEC.md` — what Navin wants to build and why (product vision).
3. `docs/roadmap/ROADMAP.md` — phases, gates and the task list from Task 037 onward.
4. `docs/bie/BIE_MASTER_SPEC.md` and `docs/bie/ARCHITECTURE.md` — the original engineering constitution.

## The owner

- Navin (GitHub `SEENAV01`) owns BIE. He runs an online coaching and directs the work through AI; he is not a programmer.
- Talk to him in simple Hinglish. Keep it short and honest; never inflate progress.
- Before each task, show a short task card: what will be built, what he will see, how we know it is done.
- After each task, show real output (a script, a video, a game, a report), not only test counts.
- He works from a tablet and a low-end 4 GB laptop. Never ask him to run builds, tests or renders locally; do heavy work in the cloud workspace or GitHub Actions.
- Decisions that are his: product scope, which book or subject first, model choice after the blind test, budget, teaching-quality verdicts, approval of security-sensitive changes and of process changes such as the fast lane.

## The product in one paragraph

BIE turns any book or PDF into a complete, world-class course: cinematic animated video lessons with
narration, a playable revision game from the same lesson, and assessment, for learners from class 1 to
postgraduate and competitive exams, in six languages, at a scale of 4–5 books of ~300 pages a day. BIE is an
orchestration "teaching operating system": it owns the teaching method, structure, checks and rendering, and
uses AI models (Claude, GPT, Gemini, local) as replaceable engines through `bie/model_gateway/`. No raw
Book → LLM → Remotion shortcut.

## Current reality (October 2026)

- The productized pipeline runs 11 stages end to end: SOURCE → DOCUMENT_INTELLIGENCE → KNOWLEDGE → PREREQUISITE → MATH → REASONING → PEDAGOGY → DIRECTOR → VISUAL → ANIMATION → SCENE_IR.
- Live AI connections exist (Task 038: Claude and Gemini through AICredits, OpenAI direct; runs only in GitHub Actions), but the thinking stages still run on regex and fixed templates.
- There is no AUDIO stage in the pipeline, and VIDEO_CODE → COMPILE → RENDER → QA and the GAME stages are not wired after Scene IR.
- Phase 1 (from 21 October 2026) builds BIE into an AI tailored to Navin's vision, section by section, judged as one whole system; read the Vision Spec section "Agreed on 21 October 2026" before any BIE work.
- Claude builds BIE; lesson content (scripts, scenes, videos, games, notes) is made only by BIE, never by hand.

## How work is done

- One task at a time, as listed in `docs/roadmap/ROADMAP.md`. Branch `task0NN-<slug>` from current `main`; open a PR; never commit directly to `main`.
- Claude merges a PR itself once all its CI checks are green (Navin approved this on 19 Oct 2026). A red check is diagnosed, never merged around.
- Never force-push, rewrite published history or delete branches you did not create.
- Update `docs/roadmap/STATUS.md` in the same PR when a task changes state.
- Before pushing from a shallow clone: `git fetch origin main` and rebase if needed.

## Engineering rules (binding)

- **Honest status words.** IMPLEMENTED is not INTEGRATED is not ACCEPTED. A simulated render is not a render; a test count is not product completion; synthetic providers prove execution, not quality.
- **Real-book proof decides.** A capability counts only when its real upstream produces its inputs and its real downstream consumes its outputs on a real book.
- **Preserve history and evidence.** `batches/`, `historical/`, `backups/`, `docs/evidence/` and the manifests under `manifests/` are immutable evidence. Earlier work is continued, never recreated from descriptions.
- **Reuse, do not duplicate.** Sections 14–18 already provide AUDIO (`bie/audio/`), GAME (`bie/game_engine/`), QA, EVAL and the operator app (`apps/operator/`, `apps/web/operator/`). Extend them instead of building parallel systems.
- **Working source** is `bie/`; applications are in `apps/` (`api`, `android`, `operator`, `web`); `app/bie` is compatibility code only.
- **Secrets** come only from environment variables or GitHub Actions secrets. Never write keys into the repo, logs, evidence files or chat.
- **Fail closed, but stay light.** Keep checks that protect correctness; do not add new sealed-review or binding-record ceremonies for ordinary tasks.
- **Source evolution (Task 037C).** Working source (`bie/`, `apps/`, `tests/`, `tools/`, `scripts/`) may change through reviewed PRs. The adoption ledgers still verify every original archive member and every recorded before-image byte for byte, but a working-source file whose bytes differ from its adoption record is reported as "evolved", not failed (`scripts/source_evolution.py`). Ledger-recorded evidence (`batches/`, `historical/`, `backups/`, recorded `docs/` evidence and before-images, `manifests/`, `metadata/`) never evolves, and a deleted working-source file still fails. The sealed compiler amendment chain authenticates the baseline copies in `docs/evidence/source-baseline-037c/` instead of the live files. Inventory checks that forbid new files inside some sealed folders (for example `bie/qa/`, `tests/qa_*`) and a few runtime identity checks in `bie/` remain; see `docs/roadmap/STATUS.md`.

## Tests and CI

- Python ≥ 3.11 (CI uses 3.13.5). Tests are mostly `unittest`; run focused suites for what you change, for example `python -B tools/run_task036_tests.py` for the Scene IR producer.
- The full canonical gate is `python scripts/integrated_check.py` (Linux, about 40 minutes); prefer letting CI run it.
- Fast lane (Task 037B): a PR that changes only `CLAUDE.md`, `docs/roadmap/**` or `docs/vision/**` skips the three heavy gates (`post-dir-canonical-catchup.yml`, `qa-section16-combined.yml`, `section18-implementation.yml`). Any other change runs all three, plus the path-matched producer workflows. The heavy gates also run on every push to `main` and nightly. A newer push to the same PR cancels its older PR run.
- Rule FR-1 until F-08 is closed: one rerun per job is allowed only for the Section 18 independent browser gate failing with `CDP_TIMEOUT:Page.navigate` or `CDP_SOCKET_CLOSED:Page.navigate` before the first product assertion. Record every use with the run's "Section 18 browser failure" annotation in `docs/roadmap/STATUS.md`. Any other failure: stop and diagnose.
- GitHub job logs and artifacts cannot be downloaded from the cloud workspace; read run, job, step and annotation data through `gh api` (REST). Each heavy job prints a failure summary as annotations (`tools/ci_failure_annotation.py`).
- Generated Remotion projects have no lockfile; CI and the M1 render runner resolve their npm installs as of the date in `tools/npm_before.txt`. Move that date only in a reviewed PR, after checking the "Remotion tree … canary" annotation.

## Historical files

`AGENTS.md` (Codex instructions), `BIE_CONTEXT_HANDOFF.md`, `docs/bie/CURRENT_STATE.md`,
`task_registry/continuation.json` and the root `CONTINUATION.json` describe earlier checkpoints (Sections
15–18 era). Their rules about preservation and acceptance still apply, but their "next step" text is
historical. The current position is always `docs/roadmap/STATUS.md`.
