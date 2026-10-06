# BIE-PROD-033 — Governed Pedagogy → Director production slice

This is the explicitly assigned productization continuation after canonical
Task032, not a historical atomic task identifier. The base is
`a03be5122bec109498b72bc2f7ee310251a9362f`, tree
`b750f609b050439c669c891a90d80b078e65c277`.

## Boundary and compatibility

The new immutable profile is
`source_grounded_di_knowledge_pr_math_reasoning_pedagogy_director_v1`:

SOURCE → DOCUMENT_INTELLIGENCE → KNOWLEDGE → PREREQUISITE → MATH → REASONING
→ PEDAGOGY → DIRECTOR.

Historical Task029/030/031/032 scopes remain exactly 3/5/6/7 stages. Task030
still blocks mathematical content with `math_evidence_required`. Task028's
inspection API/worker/local stack and Android are unchanged. The global graph
already declares DIRECTOR after PEDAGOGY and REASONING and is not changed.

The stage publishes the exact native `director.plan` ArtifactEnvelope, version
`1.0.0`, with native payload schema `bie.dir.annotated_plan/1.0.0`. There is no
productization Director payload schema or rewritten Director engine. The stage
uses `DirectorProductionAssembly`, its `DirectorStageExecutor` and canonical
registration, `load_director_inputs`, factual/source QA, hierarchical annotation
and independent review, revision/currentness and durable recovery machinery.

The exact persisted Task032 native RE projection and PED envelope are imported
by immutable reference into the Director index, not regenerated. Task032's
original producer RE artifact is independently verified and remains bound in
PED ancestry metadata and the outer stage receipt. The source catalogue and
actual PDF bytes are revalidated before providers execute.

## Governed configuration and providers

Admission requires an explicit private producer configuration: title, language,
four provider/model/adapter identities and evidence kind. No production title
or English fallback exists. The lesson ID is the actual bounded single-lesson
ID in the verified Task032 plan; instructional units do not become invented
chapters/courses. Title/language originate from explicit governed configuration.

`DirectorProviderStack` accepts configured provider-neutral canonical
ModelProvider implementations and native AnnotationRuntime. All transports must
honor their gateway deadlines. No vendor, API key or second gateway is selected
by this adapter. Missing configuration/providers block or fail closed.
The trusted test child requires `--technical-test-providers` explicitly; it is
not a default production provider. Its source-quote protocol providers operate
on actual extracted source and exact native binding IDs, and are labelled
`SYNTHETIC_TEST`. Their judgments are not live quality/calibration evidence.
Configured-provider invocation is recorded separately. An injected provider
identity does not itself prove a live/network transport call, so that receipt's
`live_provider_executed` remains unknown (`null`) unless it is the explicitly
credential-free synthetic path (`false`). Safe status preserves this distinction.

Native default policies are unchanged: temperature 0; generation retries 2,
stage attempts 3, request 96,000 characters, response 64,000 characters,
128 scenes, 1,024 total beats and 240,000 spoken characters. Semantic and
annotation policies are likewise unchanged. Oversized indivisible context
fails; no content truncation or budget widening is introduced. Windowed and
contextual Director capabilities remain native and preserved by regression,
not reimplemented by the producer.

Native QA blockers prevent publication. Native critic/reviewer transport or
schema failures can retain a review-only component internally; this governed
outer producer additionally rejects stage success if those execution failures
are nonempty. Private native attempts remain durable for diagnosis. A model
cannot certify acceptance: output retains `requires_review=true`,
`accepted=false`, `release_ready=false` even when DIRECTOR succeeds.

## Mathematical teaching limitation

Task032's exact baseline native PED inputs contain EXPLANATION bindings and no
`teaching_context_ref`; the RE projection reports teaching-order reasoning.
Those immutable inputs must not be rewritten to manufacture derivation
obligations. Simple verified equation explanation may execute, with each exact
source expression required in source-cited speech, and native factual QA.
Explicit derivation-step requirements block with
`director_math_teaching_contract_required` until exact native upstream
context/derivation obligations exist. No new math solving, new misconceptions,
learner mastery or invented adaptive history is authorized. Unsupported Math
continues to block before Reasoning/Pedagogy/Director; no provider is invoked.

## Storage, identity and recovery

The existing CAS, SQLitePersistence, durable queue, outer idempotency,
EnterpriseOrchestrator and fencing remain the pipeline infrastructure.
`director-catalog.sqlite3` is the existing native SQLiteArtifactCatalog index
inside the same governed run namespace, over that same CAS. It cannot use the
outer run-store file because the two canonical artifact tables differ.
`director-state.sqlite3` holds native Director idempotency/revisions/recovery
leases, not pipeline run state. It cannot share the outer lease transaction.
The outer SQLitePersistence is the sole overall pipeline/stage authority.
Task033 reuses one owned SQLite connection only for inherited artifact-record
reads within each synchronous service call; it caches no rows or CAS bytes.
Every query remains the canonical `SQLitePersistence.load_artifact` query and
sees current committed SQL. Database path/inode replacement and nested reads
fail closed. Writes retain fresh canonical connections, including operation-local
`total_changes` semantics. Service shutdown closes the read connection. The
historical profiles retain their original `ClosedPersistence` factory.

Exact native output envelope IDs, original CAS bytes and ordered parents are
bridged into the outer artifact index. No competing semantic payload/alias is
published. Ordered native parents are explicitly retained because outer SQL
stores parent sets in sorted order. Every index/CAS/reference is verified.
Native evidence containing narration/source excerpts is PRIVATE, even when its
native evidence flag is true. Only bounded `SAFE_EVIDENCE` receipts may be
uploaded; flags alone are not a privacy classification.
Committed status also validates the native idempotency replay CAS receipt with
the existing executor parser/ancestry checks and binds its exact output,
evidence, metadata and review diagnostic. An orphaned output cannot conceal a
missing, foreign, failed or tampered replay record. Admission rejects mixed
explicit configuration and provider/model overrides rather than ignoring one.

Idempotency binds exact RE/PED refs, governed configuration, providers,
policies and native code fingerprint. Same intent replays the native committed
result without provider calls. Changes conflict or require an explicit native
revision/previous identity. Outer interruption attempts and native revisions
are distinct: outer recovery retains failed attempts and re-enters native
attempt 1 with its original key so native recovery may reclaim an expired
incomplete claim or replay the exact committed result. No live lease is stolen.
Provider execution is not a distributed exactly-once transaction. CAS/index/
state/ACK boundaries are verified and recover explicitly, not in a retry loop.

## Section18 and downstream

`DirectorProducerControlPlane` follows existing authenticated profile delegation
and worker reservations. Tenant/resource/private-path/permission checks remain
native Section18 controls. Unsupported pause/cancel remains fail-closed.
Safe projections expose identities/counts/review status, not textbook text,
narration, prompts, raw responses, traces, credentials or filesystem paths.

No canonical Visual input loader for the exact persisted
`director.plan + reasoning.decision_set` envelope pair was found. Existing
Visual codecs consume authored legacy handoff/intents/timing packets; the
native Director consumer validates current output but cannot prove that missing
next-stage composition. Visual compatibility is recorded as NOT_AVAILABLE,
not fabricated as PASS. VISUAL, ANIMATION, SCENE_IR, VIDEO_CODE, compiler/render,
GAME and every later graph stage remain NOT_RUN.

Director textual narration is not TTS/audio generation or synchronized media.
AUDIO graph reconciliation remains OPEN. QA16-GAP-030 remains historically
unchanged. Technical source-derived protocol execution does not establish
academic correctness, teaching effectiveness, real learner mastery, rendered
media, playable games, deployment/security or product acceptance.

## Validation

`tools/run_task033_tests.py` selects new and inherited tests once per lane;
receipts expose counts and failing test names only, not private traceback data.
`scripts/smoke_bie_director.py` runs genuine generated PDFs in actual bounded
children for supported equations, explicit non-Math and unsupported-Math
fail-closed cases, then reopens state in a second process. Native artifacts,
provider/QA/annotation calls, exact replay and queue ACK are verified.
The hosted Ubuntu workflow is credential-free and uploads safe JSON only.
Full canonical Linux PR preservation remains required before any merge.
The serialized local Task033 lane passed 117 unique authored tests (85 producer
controls and 32 recovery/persistence controls), with zero failures, errors or
skips. This is technical local evidence; hosted/full-canonical acceptance is
separate.
The selected affected Windows lane observed 3,148 tests, 81 failures, 57 errors
and zero skips. All 683 tests across the 72 native Director modules passed.
The two lanes therefore cover 3,265 selected test executions without adding
baseline comparisons or repeated diagnostic runs to that total. The affected
lane is NOT green.

Retained unchanged-base receipts reproduce the shared QA/Math/readiness,
Pedagogy QA/repair and path-normalization failure identities where recorded.
Pedagogy baseline aggregates differ and are not generalized as identical.
An additional comparison on clean exact canonical `a03be512` ran the 255
Director QA/repair tests: 34 failures, 16 errors, zero skips, versus 33 failures
and 16 errors for that candidate subset. Every candidate failed method appears
in the baseline; the baseline additionally fails
`test_native_dependency_content_identity`. This is qualified reproduction
evidence, not proof of the precise cause of each failure. The primary checkout
remained clean. No tests or native engines were weakened to force Windows green.

Windows full canonical green is not claimed. Earlier platform/path/long-path,
QA and isolated non-reproducing failures remain evidence; this task neither
waives them nor assigns their causes without proof.
During concurrent local validation, bounded child runs reached the unchanged
45-second wall deadline without stdout; one persisted snapshot stopped in
REASONING, before PEDAGOGY/DIRECTOR. A byte-identical short-path source copy also
reproduced a bounded failure under load. Neither observation proves an
underlying cause or a Director-specific regression. These results are retained,
and final resource-sensitive validation is serialized without budget widening.
Another quiet pre-adapter run committed all eight successes/ACKs but reached
the same deadline before stdout; it is also retained as a failed smoke, not a
restart proof. After the read-ownership and replay-verification changes, a
hash-identical source copy passed all three bounded journeys and their actual
second-process restarts. This establishes technical execution for that revised
source, not the precise cause of every earlier failure or Windows full-green.
The source audit reported four historical long-path mismatches on Windows;
extended-path reads of all four match both the ledger and the base Git blob
identities. The failed audit is not relabelled green.
