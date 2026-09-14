# DIR grounded execution — batch 008

Current additive checkpoint: **BIE-DIR-HARD-DIRECTOR-001**. The original checkpoint
remains BIE-DIR-QA-007, with 37 original entries implemented. This batch adds
BIE-DIR-HARD-INPUTS-001 and BIE-DIR-HARD-DIRECTOR-001 for concrete audit findings.
The original 867-row roadmap and recovered product vision are unchanged.
**DIR section implementation is incomplete; BIE is NOT ACCEPTED.**

## Implemented boundary

`DirectorArtifactIO` uses the existing ArtifactEnvelope, ArtifactRef,
FileSystemCAS and ArtifactCatalog. It checks actual bytes, canonical envelope
hashes, full parent references, source/block provenance, graph acyclicity and
run identity. No parallel artifact or orchestration framework is introduced.

`publish_source_catalog` wraps supplied extraction and actual source bytes into
source.document, source.block and document.source_catalog envelopes. UTF-8 text
must exactly match its complete one-page source. Non-text extraction retains
review. This adapter does not execute PDF/OCR or replace document.structured.

`publish_reasoning` preserves canonical ReasoningDecision objects and optional
GroundedResult artifacts. Evidence IDs must resolve to actual source.block
artifacts; friendly passage aliases cannot substitute for artifact references.
`publish_pedagogy` preserves canonical UnifiedPedagogyPlan, LearningObjective,
TeachingModeDecision and AssessmentCell values with explicit teaching bindings.
Those bindings contain lesson/objective/RE IDs and actual mode/assessment outputs;
they contain no scene plan, narration or QA receipt. Source, RE and PED references
must describe the same revision and run. Upstream review cannot be cleared by a
model response. Cross-lesson prerequisites require an explicit bridge and currently
fail; the adapter does not assume that an earlier lesson was mastered.

`execute_grounded_director` reloads the canonical parent graph before generation.
It calls the injected canonical ModelProvider for PLAN and then each NARRATE
operation. The payload contains the relevant evidence and complete cited pages,
resolved RE dependency closure, actual PED decisions and previous narration.
Strict responses must preserve revisions, evidence, objectives, modes,
prerequisite order, teaching moves and every supplied assessment obligation.
Assessment questions, answers and success criteria become actual spoken content.

Generated speech is compiled into the existing lesson/script/snapshot contracts,
TIME speech/pause/emphasis/timeline objects and game-learning handoff. Each entire
utterance receives conservative FACT coverage and the existing factual critic
executes through its own injected provider. BIE recomputes source, factual,
coherence, repetition, audience and pacing QA; a model cannot submit acceptance.
Empty detailed annotation inputs retain the existing review findings.

`DirectorStageExecutor` registers through `register_director_stage` with the
existing EnterpriseOrchestrator and canonical DIRECTOR contract: predecessors
PEDAGOGY + REASONING, inputs pedagogy.plan + reasoning.decision_set, output
director.plan. Configuration under `director` is exactly lesson_id/title/language.
Providers, identities, policies, ArtifactCatalog and SQLiteIdempotencyStore are
injected by the application. The helpers do not modify the canonical registry on
disk or configure a live application automatically.

## Execution, persistence and repair behavior

Model retries are bounded to at most three per phase; default two. Every actual
request/response attempt has a phase, subject, fingerprint and outcome. Refusal
or identity mismatch stops immediately. Missing inputs stop before model calls.
Provider exception details are excluded from operational receipts. Character,
scene and beat budgets fail explicitly without truncating educational content;
they are resource bounds, not a lesson-duration target or mandatory template.
Transport-level timeouts and model token limits belong to the injected gateway.

SQLite idempotency binds run, inputs, configuration, model/policy and code to the
stage key. Completed success and failure replay persisted, hash-verified evidence
without additional provider calls. A conflicting key fails. An in-flight claim
requires infrastructure recovery; it is not blindly rerun. Stage attempts are
also bounded. This is not a transaction across a model service, CAS, catalog,
SQLite and the orchestrator. Crash recovery, durable catalog-index restoration,
cross-worker coordination and dependency-aware invalidation remain open integration
work; no exactly-once external model execution guarantee is claimed.

Evidence is persisted as evidence.director_execution. QA blockers persist the
candidate/evidence and fail the stage without publishing director.plan. A review
candidate can complete the component stage, but is always requires_review=true,
release_ready=false, accepted=false. Missing/invalid input errors have actual
CAS operational receipts, not invented source provenance. Success/failure replay
records are operational CAS data, distinct from learning artifacts.

Downstream consumers must enforce the review/release boundary. The generic
orchestrator treats SUCCEEDED as scheduling readiness and does not implement
that product-release policy. Actual consumer gating is still required before
connecting this stage to production VIS/ANI/compiler or game execution.

## Verification and limits

Run from the combined ZIP:

```bash
python scripts/check_dir_execution.py
python examples/grounded_director_walkthrough.py --output verification/grounded_director.json
```

The current suite has 384 tests in 47 files: 286 original DIR regression,
52 earlier hardening tests, 18 new input tests, 18 new directing tests and
10 new executor integration tests. No old source or test is edited this batch.
The separate pinned canonical gate has 2,160 tests in 551 files and still does
not discover staged DIR tests.

The walkthrough executes authored science, economics and fictional-history
cases with respectively two, one and three scenes. Canonical teaching_order,
objective generation, teaching-mode selection, assessment blueprint and pedagogy
plan functions execute; the history case additionally runs canonical temporal
event_order and retains its actual GroundedResult. The supplied curriculum
readiness signal is fixture data, not a measured learner profile or questionnaire.

Nine generator calls and fifteen critic calls execute against explicitly
preauthored protocol providers. All cases remain REVIEW_REQUIRED. No live model,
real-book pipeline, audio/video render, simulation runtime or playable game ran.
These are execution/wiring tests, not evidence of enterprise teaching quality.

The adapter currently handles grounded source-block RE evidence and supplied
canonical PED values. Rich KI claims, derived math artifacts, prerequisite/mastery
bridges, retrieval/chunking and all PED payload families need further codecs and
production assembly. Assessment blueprint checks establish consistency with the
supplied cells, not independently sufficient pedagogy or learner mastery.

DERIVATION requires a bound upstream mathematical_derivation decision; SIMULATION
requires a demonstration move. These checks do not verify a mathematical proof
or run a simulation. Derivation, experimentation, Socratic dialogue and misconception
teaching need broader implementation and independent evaluation. Full-utterance
FACT coverage is conservative: source-literal numeric checks can flag a valid
derived result, and questions can remain semantically uncertain. Fine-grained
claim/discourse/audience/repetition/emphasis/pacing producers and evaluators are
the next DIR work; prompts alone do not close those requirements.

## Preservation and continuation

The combined package retains all 37 original ZIPs and four additive hardening
ZIPs. Apply original dependency closures first, then hardening overlays in
dependency order; old originals must not overwrite prior contract corrections.
Atomic ZIPs declare task and canonical file dependencies and are verified in
fresh isolated extraction directories. The combined workspace is the convenient
runnable delivery. The code fingerprint covers all present `bie/**/*.py` files;
a smaller atomic dependency closure therefore has a different code identity.

Keep the original video AND playable-game vision, evidence/provenance, structured
IR, replaceable providers/tools, explicit uncertainty and governed cumulative
PDF learning. No mandatory learner questionnaire, arbitrary duration cap,
universal scene template or raw Book-to-LLM-to-Remotion shortcut is introduced.
See CAPABILITY_AUDIT.md for open implementation work. After required hardening
and re-audit, perform lossless canonical GitHub integration in this chat.
