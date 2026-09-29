# Batch 007 — Director QA implementation specification

## Identity and product purpose

This additive batch implements the bounded declared-plan/text portions of the original
Section 16 tasks BIE-QA-DIR-001 (narrative coherence), 002 (script quality), 003 (pacing)
and 004 (source fidelity), on page 17 of the original 18-section master registry.
The implementation lives in `bie/qa/director_v2`; none of the earlier QA namespaces
or native engine implementations is replaced. Section 15 belongs to another work
session. This package is a cumulative Section 16 lane package, not a full repository.

BIE's intended output remains accurate, understandable, cinematic educational video
and meaningful playable learning experiences. This evaluator must not reward a hook
with no explanatory payoff, dramatic language that loses source conditions, a title
masquerading as teaching, or attractive timing metadata with no inspectable text.
Conversely, these plan checks do not measure cinematic quality, engagement or learning.
Those outcomes require later actual-media evaluation and real-book/learner evidence.

## Inputs and authority

`DirectorRequest` contains the existing `source_v2.Request`, learner/language/lesson
scope, required scenes, timed beats, finite routes, transitions, promises, term
introductions, optional expanded spoken forms and source-transformation mappings.
The existing source request references actual source and output bytes, exact Unicode
codepoint offsets, citations, source blocks and artifact identities.

`DirectorPolicy` is supplied by the operator outside the candidate. It declares
approved scene membership and dependencies, allowed scene roles, route objectives,
source facets and their conditions, vocabulary/assumed knowledge, required promises,
timing constraints and language/audience-specific limits. A candidate cannot lower
its own threshold, omit an approved branch, redefine the intended learner or change
the source facet inventory. Route scene sets are governed; actual route order is
checked against required dependencies and narrative constraints, not against native
record-sort order. Every explicit route is checked separately.

All dataclasses are frozen and use exact types and closed vocabularies. Booleans do
not count as integers. Unknown JSON keys, duplicate JSON keys, non-integer numbers,
unknown versions, duplicate entity IDs and excessive collections fail validation.
Three JSON schemas cover request, policy and review structure only; runtime checks
add bounds, references, authentication, provenance and semantic plan constraints.

## Executed dependency path

`evaluate` reruns `source_v2.evaluate` on source/output files; it never trusts a
supplied PASS report. Missing, modified, unsafe or mismatched bytes produce source
failures that propagate to all four Director reports. The optional source assessor
is supplied separately, using the existing source assessment verifier.

The actual native `build_lesson_architecture` and `build_script_plan` are invoked
through `adapters.to_native`, and their validators and fingerprints are used.
Native architecture and contract-validation files are inherited byte-identically.
`bie/director/script_plan.py` is the one newly added standalone dependency, obtained
from the GitHub connector at commit 375d99af0edd0086206817dae932156ddf61c569; its Git
blob, SHA-256 and length are checked. Native builders sort records by ID. That order
is not promoted into a playback schedule. Native review flags are not acceptance.
These snapshots are VERIFY ONLY during eventual integration, never overwrite sources
in a newer canonical HEAD without reviewed reconciliation.

## Contextual assessment boundary

Scene teaching quality, script-to-meaning mapping, transitions, payoff relevance,
term explanations, source transformations and audience suitability require current,
purpose-scoped, authenticated assessments. `reasoning_v2` review authentication is
reused for signatures, evaluator/version/purpose authorization, time bounds and
independence groups. Request and policy digests bind the whole plan. Review target
and evidence sets must match exactly. Missing, uncertain, low-confidence or test-only
review keeps the result at REVIEW_REQUIRED. Invalid or rejected review blocks it;
additional approvals cannot outvote a rejection. Repeated identities cannot create
an independent quorum. Authentication proves who issued an assessment under the
configured key policy; it does not prove that the semantic judgment is correct.

Positive tests use explicitly synthetic HMAC keys, including simulated operator-managed
keys. No production credential or live reviewer service is bundled. Source grounding
and Director assessments are separate: one cannot substitute for the other. The CLI
has no operational signing-key loading path and cannot authorize production release.

## DIR-001 narrative coherence

Every required scene has actual script content. Teaching beats name objectives within
their scene. Each route has its approved opening/closing roles and explanatory
coverage. Dependencies must finish before dependent scenes begin. Every adjacent
scene pair has one source-inspected transition in the destination's first content
beat; duplicate, unused and out-of-scope bridges do not count. A declared hook/problem
must have a later nonidentical explanatory payoff on every route containing the setup.
A recap must follow teaching; a hook, question or mention alone earns no explanatory
credit. The reviewer determines whether the explanation truly answers the question.

## DIR-002 script quality

Checks use actual output spans, not just a `text_intent` string. Overlapping spans
are unioned without double counting. Conflicting overlap blocks evaluation. All
output claims must be represented in the beat/readout inventory. Draft markers,
hidden direction overrides, replacement characters and invalid controls are caught.
Literal normalized repetition requires a permitted recap/retrieval/feedback/emphasis
purpose and an earlier same-route reference. This is not semantic paraphrase detection.
Declared technical terms must appear in an authorized explanatory introduction before
use, or be explicitly designated assumed knowledge by the operator. Expanded spoken
forms are included in this vocabulary check. One declared speaker cannot silently
switch voice identity. Sentence-length thresholds are diagnostic review guardrails,
not an independently validated age/readability or comprehension score.

## DIR-003 pacing

Integer millisecond boundaries define half-open intervals. A beat must fit inside
its scene. Non-whitespace Unicode codepoint counts and exact rational rates are
computed from inspected text. These are not words-per-minute and are not empirical
speaking/reading measurements. Multiple simultaneous speech or on-screen text streams
are checked for both allowed count and combined rate; low individual rates cannot
hide a high combined peak. Speech cannot occupy a declared reflection pause. Leading,
internal and trailing unmotivated gaps, excessive explicit pauses, route budgets and
operator response/reflection minimum/maximum timing constraints are evaluated.

Mathematical notation triggers a reviewed expanded readout requirement. Expanded
speech must bind actual narration output claims and exact inspected text; a metadata
annotation alone remains REVIEW_REQUIRED. Expanded claims also need source-fidelity
mappings. The pacing calculation uses the larger of raw and expanded text costs so
that a deliberately shortened expansion cannot reduce the original text budget.
Actual TTS durations, pronunciation, within-beat word alignment, audible pause lengths
and final video synchronization are not established by this implementation.

## DIR-004 source fidelity

Each output/readout claim declares a transformation: exact quote, paraphrase,
simplification, analogy, hypothetical, question or instruction. The cited anchors
must be those attached to the claim; mandatory source facets specify permitted
transformations. A changed quotation is blocked even with a positive synthetic
review. A factual claim cannot evade assessment by changing its transformation label
to question/instruction. Required source conditions cannot be omitted or renamed.

Conditions and nonliteral disclosures need separate, nonoverlapping, source-inspected
claim spans, presented locally in the same scene at or before the primary beat and
within the operator qualification window. Every repeated presentation is checked.
This is beat-level visibility, not token-level audible ordering: within-beat sequence
and human comprehension remain media/assessor obligations. Self-citation or a condition
shown later in another scene does not satisfy the check. Analogy/hypothetical content
requires explicit reviewed disclosure and cannot by itself replace a required factual
explanation. Each route must teach all required source facets.

## Reports and release behavior

Four deterministic `source_v2.Report` values contain original task IDs, findings,
severity, subjects, measurements, inspected artifact IDs, limitation statements and
request/policy/evidence digests. `verify_reports` recomputes rather than accepting an
edited result. A report can be BLOCKED, REVIEW_REQUIRED or CHECKS_PASSED only within
this declared-plan/text scope. There is no product acceptance state.

`prepare_release_evidence` validates the candidate run/revision/digest, exact source
inventory and artifact identities, recomputes the checks and returns report bytes
plus an unsigned `GateEvidence`. It does not write/sign a report or modify a repository.
The existing full `director_quality` media gate receives FAIL when blocked and NOT_RUN
otherwise, never PASS. The actual inherited ReleaseEvaluator rejects the incomplete
bundle. Fake video/game files in the authored test fixture are explicitly marked
NOT_A_RENDER/NOT_A_GAME and are not inspected as media evidence.

## Bounds and safety

Up to 256 scenes, 1,024 beats and 32 finite routes are admitted; integer time is capped
at one day. The evaluation has a 16-million-codepoint text-work admission limit.
JSON has size/depth/collection limits, and source artifact reads reuse existing
filesystem confinement. Actual worker CPU/memory/time envelopes, Windows variants,
time-of-publish TOCTOU protection and production storage/trust remain integration
obligations. Declared finite routes do not prove executable game reachability or
coverage of unenumerated branches/loops.

## Verification and residual work

Read the executed receipt, individual test IDs and logs at
`evidence/qa_section16/executed_run_007/`. Targeted safeguard-removal probes are under
`mutation_run_007`; they are not exhaustive mutation coverage. Prior unsuccessful or
superseded development attempts remain under `development_007`, including an outer
command timeout, corrected test attribute names and a strengthened short-readout
fixture identified by a surviving mutant. Final runs do not add earlier reruns to
the unique test count.

The gap ledger retains native PDF/OCR extraction, real semantic provider operation,
reference validity, actual video/audio/game correspondence, multilingual calibration,
learner studies, cinematic quality, canonical callers, full-repository regression,
section audit/hardening and real-book E2E acceptance as open where not proven.
This batch does not close those obligations merely by authenticating test fixtures.
