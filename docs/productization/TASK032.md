# BIE-PROD-032 — governed Reasoning to Pedagogy plan

This is an explicitly assigned continuation after canonical Task031. Base main
is `92ac498711f6bda8eb5ac90323fe486b4e802a86`, tree
`57ed59a16a3416e69d4c5a017ae1600a27073053`. Technical implementation and focused
evidence do not establish canonical integration, academic correctness or product
acceptance. Full canonical Linux preservation remains required before merge.

## Versioned composition and scope

The new profile `source_grounded_di_knowledge_pr_math_reasoning_pedagogy_v1`
executes exactly SOURCE, DOCUMENT_INTELLIGENCE, KNOWLEDGE, PREREQUISITE, MATH,
REASONING and PEDAGOGY. It extends the existing durable producer. Task029 remains
exactly three stages, Task030 remains exactly five, and Task031 remains exactly
six. Historical Task030 math-dependent Reasoning still blocks with
`math_evidence_required`. Profile and persisted scope mismatches fail closed.

The global execution graph is unchanged: its existing REASONING to PEDAGOGY
contract emits `pedagogy.plan`, which the existing Director already consumes
alongside `reasoning.decision_set`. DIRECTOR and every later stage remain NOT_RUN.
No narration, script, scene, animation, audiovisual code or game is generated.

One Task032 plan is a run-level, bounded single-lesson plan containing multiple
instructional units. It is not a full book curriculum. Each instructional unit
has a real concept/objective and upstream evidence. Bounds are explicit producer
policy. A book exceeding this slice's supported size/scope requires review or a
later governed course-assembly/decomposition capability; it must not silently
lose source coverage or become one unbounded lesson.

## Native Pedagogy composition

Canonical native objective, prerequisite-aware sequencing,
assessment/mastery planning, cognitive-load, provenance and plan
contracts are composed. Their source remains unchanged. Objective bindings
refer to verified Knowledge concepts and authoritative upstream evidence.
Canonical prerequisite dependencies constrain teaching order; original source
order is retained independently. Deterministic tie-breaks and load values are
technical heuristics, not measured instructional optimality.

The bounded credential-free producer is labelled TECHNICAL_SOURCE_DERIVED.
Requires-review/uncertainty from the upstream chain remains visible and cannot
be promoted into semantic acceptance. A planned assessment or mastery criterion
is not an observed learner result. No learner profile, past attempts, diagnostic
scores, adaptive transitions or measured mastery are fabricated. Learner-specific
adaptation needs real governed learner input in a later task.

Misconceptions and conceptual confrontation require actual upstream or governed
evidence. Absence of such evidence does not justify invented misconceptions.
The plan records supported requirements rather than filling every pedagogical
category. Explanation, practice and assessment structures remain plans, not
generated teaching content or final narration. Unsupported candidate fields or
generic unbounded assertions fail validation.

## Grounding and Math

Admission requires the exact verified successful Reasoning artifact belonging
to this run and source. Knowledge, Prerequisite and Math contexts resolve through
verified artifact ancestry. Private artifacts bind run/source and exact upstream
IDs/hashes, producer/schema/policy identities, attempt and evidence. Foreign or
tampered inputs, invented concepts/anchors/evidence, invalid prerequisite order
and overstated certainty cannot unlock Pedagogy.

Math is consumed and revalidated; its evidence and identity are never rewritten.
REQUIRED retains verified Math obligations.
NOT_REQUIRED supplies an explicit applicability artifact and cannot introduce
invented Math teaching. REVIEW_REQUIRED/BLOCKED Math cannot unlock successful
Reasoning or Pedagogy. Unsupported Math remains governed review evidence.

## Director compatibility without execution

The native ArtifactEnvelope contract requires UUID run identities. Task032
therefore admits a deterministic UUID5 derived from its profile, tenant and
idempotency key as its actual producer run ID. A versioned identity-validation
hook preserves the original `prod-...` identities for Task029/030/031. There is
no second run or translated run identity. The global graph remains unchanged.

The stage artifact is the native `pedagogy.plan` envelope with semver `1.0.0`.
Its private instructional metadata uses `bie.pedagogy.plan/1`; the payload keeps
the exact native source_catalog_ref/reasoning_ref/plan/objectives/bindings shape.
Native envelope records are stored through the same SQLitePersistence artifact
table and CAS. The stage record and native envelope reference the same content;
the stage record additionally binds the exact original producer ancestry.

The verified Task031 Reasoning decision values, IDs, confidence and uncertainty
are retained. Its Knowledge/Prerequisite/Math evidence references are expanded
deterministically into their verified original DI source-block references for
the canonical Director source-catalog codec. The unmodified upstream Reasoning
artifact ID/hash and all other upstream identities remain bound in the private
Pedagogy metadata and safe receipt. This is a representation conversion, not a
new reasoning execution or an additional semantic assertion.

The persisted plan and Reasoning decision set are checked using the actual
canonical Director input loader/validator. The existing canonical typed codecs,
artifact envelopes, source catalog and provenance contract are used; an adapter
around the existing SQLitePersistence/CAS resolves durable producer artifacts
into that contract. The adapter does not create new pedagogical content, bypass
the validator, fabricate an accepted envelope or execute Director.

This boundary proves structural consumer compatibility only. It does not prove
Director quality, lesson effectiveness or acceptance. Compatibility checks
preserve technical-review flags, original source identity and private source
catalog data; routine projection and evidence remain safe.

## Durability and privacy

Existing CAS, SQLitePersistence, SQLiteDurableTaskQueue, SQLiteIdempotencyStore,
EnterpriseOrchestrator, fenced leases and recovery semantics are reused. No new
queue, run database architecture, CAS, orchestrator or model gateway is added.
Stage capabilities preserve Task028 worker isolation and operator namespaces.
ACK follows verified artifact publication, evidence and terminal stage commit.
Idempotent replay preserves committed identity; conflicting intent fails closed.
Explicit recovery preserves interrupted attempts around candidate generation,
CAS publication, stage terminal commit and queue ACK. No distributed cross-store
atomicity or automatic redrive guarantee is claimed.

Private textbook text stays in runtime CAS artifacts/catalogs. Safe status and
receipts expose counts, hashes, stage state, review codes and bounded identities.
They do not contain source text, prompts, equations, credentials, filesystem
paths or raw tracebacks. Ordinary hosted CI uses generated native PDFs without
live provider credentials and uploads safe JSON receipts only.

Section18 remains the governed control plane. Its new explicitly enabled
Task032 profile delegates to the canonical producer. Existing inspection and
Task029/030/031 profiles retain their contracts and controls. Unsupported controls
remain fail closed. Android and Task028 runtime semantics are unchanged.

## Verification and remaining gates

Run `tools/run_task032_tests.py --lane new` and `--lane affected` with safe output
files, then `scripts/smoke_bie_pedagogy.py`. The affected selection inherits every
Task031 authored/affected test and selects all canonical Pedagogy original,
hardening and integration modules, Director input/context/codec contracts and
relevant Section16 Pedagogy QA/repair tests. A test module appears only once;
repeated execution never inflates authored or total counts.

The real-process smoke requires the seven-stage source-derived journey, exact
artifact ancestry, persisted evidence, ACK and idempotent replay, then reopens
the state/artifacts in a second actual process. It also checks canonical Director
input compatibility while DIRECTOR remains NOT_RUN. Hosted Ubuntu uses the
existing approved dependencies/actions and separately runs historical Task029,
Task030 and Task031 smokes plus canonical source preservation.

Windows inherited path, POSIX/resource and long-path evidence remains retained;
Windows full-canonical green is not claimed. A platform failure must be attributed
from evidence, not labelled a new producer regression or silently waived.

Local Task032 verification recorded 81 new tests passing with zero failures,
errors or skips. The disjoint affected selection ran 2,244 tests with 48 failures,
42 errors and zero skips; it is NOT green. Native Pedagogy (141), Director (115)
and the selected Section18 (226) tests passed. Shared Pedagogy QA/repair failed
method identities were reproduced on unchanged main, with differing aggregate
counts retained separately. The inherited Task029 terminal-before-ACK error did
not reproduce in isolated base/candidate checks; its cause remains unproven.
These observations do not attribute every broader failure.

The final standalone supported-Math, non-Math and unsupported-Math process
journeys passed with the unchanged process limits, second-process identity
checks and positive-path Director input validation. An earlier concurrent
standalone invocation reported `child_supervision_incomplete`; that observation
is retained and its precise cause is not claimed. No retry loop, timeout or
output-budget increase was introduced. Repeated execution adds no authored tests.

The required broad integrated gate stopped at its first source verifier on four
Windows paths of 260--266 characters. Extended-path reads matched the preservation
inventory for all four. Later gates did not run; full canonical local PASS is
NOT claimed. Governed hosted Linux preservation remains required before merge.

QA16-GAP-030 remains OPEN / technically narrowed under its historical record.
AUDIO graph reconciliation remains OPEN. No native Math/Pedagogy/QA/Evaluation
architecture, historical archive or original atomic task ID is rewritten.

Academic correctness, empirical teaching effectiveness, actual learner mastery,
complete course assembly, Director/script execution, audiovisual quality, game
generation, public deployment, enterprise security and whole-product acceptance
remain open. No PR, merge or Task033 is authorized by this implementation task.
