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
5. **PR → CI → merge** — Navin merges (or Claude, once Navin allows merging on green CI).
6. **Update `docs/roadmap/STATUS.md`** and show the next task card.

## Phase 0 · Foundation (about 2–3 days)

**037A · Repository memory** — `CLAUDE.md`, Vision Spec, this roadmap and the status file in the repo.
Docs only; no code changes. Done when merged.

**037B · Fast lane and CI debts** — needs Navin's approval first.
- Today every PR to `main` runs three all-path heavy workflows (Post-DIR canonical about 45 min, Section 16 QA combined, Section 18 about 42 min) plus the matching producer workflows, even for a documentation change.
- Proposal: documentation-only changes skip the heavy gates; each PR runs the gates relevant to the paths it touches; the full canonical gates run on merge to `main`, nightly and before a release. No gate is weakened, deleted or made non-blocking for code it covers.
- Fix F-08 (Section 18 browser `CDP_TIMEOUT:Page.navigate` before the first product assertion) with a found cause and a regression test, not repeated green runs.
- M1 `verify` takes 35m35s of its 45 min limit; split it or justify a new limit with timing evidence.
- Done when: docs-only PRs finish in minutes, code PRs keep full coverage, F-08 has a cause and a test.

**038 · Live AI and the blind test**
- Real provider adapters (Claude, OpenAI, Gemini) behind the existing `bie/model_gateway/` interface; keys only from environment or GitHub Actions secrets, never in the repo or chat.
- Structured output with schema validation, bounded retries, response caching, and token and cost logging per call.
- A deterministic fake provider keeps every existing test offline and repeatable.
- Blind-test harness: one real chapter → lesson plan, narration script and 5 questions per provider → anonymised A/B/C report for Navin.
- Gate: Navin picks the main model (and optionally a cheaper checker model).

## Phase 1 · First real chapter (about 2 weeks)

**039 · Understanding the book with AI** — KNOWLEDGE, PREREQUISITE and REASONING stages call the model:
concepts, definitions, relationships, prerequisites and misconceptions, each anchored to source text and
checked by a second pass. Replaces the regex candidate scan and template logic.

**040 · The teaching brain** — PEDAGOGY and DIRECTOR produce a real lesson plan and narration script with the
teaching recipe, level adaptation and story mode (wire `narrative_arc`, `hook_strategy`, teaching-mode
selection). Rubric checker plus Navin's review of the output.

**041 · Visuals from building blocks** — the first ~10 animated building blocks (Remotion components, one
house style); VISUAL and ANIMATION choose and fill blocks; multi-scene Scene IR.

**042 · Audio** — narration voice (ElevenLabs is already in `bie/audio/`; voice choice is Navin's), timing
taken from the real audio, sync of every reveal to the spoken words; resolve the open AUDIO reconciliation.

**043 · Real video** — wire VIDEO_CODE → VIDEO_COMPILE → VIDEO_RENDER → VIDEO_QA after Scene IR; render in the
cloud (GitHub Actions); frame checks; an MP4 Navin can watch.

**044 · Revision game** — GAME_DIRECTOR → GAME_IR → build → runtime → QA through the Section 15 engine; a
browser game playable on a phone, built from the same lesson.

**Gate 1:** Navin approves one chapter's video and game; his students give feedback.

## Phase 2 · World-class in one subject (about 1–2 months)

- Teaching recipe library and Navin's "gold lessons" as the quality bar; story mode for suitable topics.
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
- Then the public self-serve tool.
