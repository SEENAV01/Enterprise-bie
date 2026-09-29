# Section 16 Batch 006 — pedagogy QA specification

## Governing scope and boundaries

Original registry page 17, BIE-QA-PED-001–004. This is an additive continuation
under `bie/qa/pedagogy_v2`, not a replacement of the existing PED producer or
Sections 1–15. Section 15 is owned by another work session. No local result can
stand in for its eventual runtime and learning-alignment evidence.

The product target remains accurate, source-grounded, engaging educational
videos and playable learning games that explain complex topics well. This
batch evaluates necessary teaching-plan conditions; it does not establish that
the resulting audiovisual experience is cinematic, effective or even rendered.

## Trust boundaries

The operator supplies a PedagogyPolicy independently of the candidate. It owns
objective identities, concepts, observable actions, criteria, cognitive categories,
response modes, mastery floors, required examples/items, transfer requirements,
prerequisites, allowed route membership, spacing rules, audience/language and load
budgets. An operator-authenticated policy is assumed by the API boundary; this
batch does not create an identity-management service or a policy approval system.

The candidate supplies PedagogyRequest: the existing Source Request, objectives,
segments, events, teaching links, assessment items and explicit finite routes.
All identities, types, vocabularies, numeric limits and reference scopes are
validated. Booleans are not integers. Unknown fields, duplicate JSON keys,
nonfinite numbers, empty required scope, aliases and unsupported versions cannot
silently pass. Candidate scope cannot shrink the operator's requirements.

Source-v2 actually reads declared source/output bytes, checks their hashes,
lengths, spans and citations, and applies its existing filesystem confinement.
All declared claims must be scheduled in valid presentation events. Source QA
failures propagate to every pedagogy report. Exact quotation does not establish
contextual support; source assessments remain separate obligations.

The PR/RE ReviewVerifier is reused. Purpose-scoped reviews bind the entire
request and operator policy, exact evidence identities, reviewer/version,
freshness, key state and declared independence group. Required contextual reviews
cover inventory, objective mapping, event mapping, teaching alignment, assessment
demand/answer correctness, route completeness and load-profile applicability.
A rejected review cannot be outvoted. Missing/uncertain/test-only assessment cannot
be converted to a pass. No operational keys are built into the runtime. Public
synthetic keys occur only in the clearly labeled test fixture and demonstration.
Authentication is not independent proof of reviewer quality or independence.

## BIE-QA-PED-001 — learning-objective evaluator

Validate candidate concepts, exact allowed cognitive categories and all observable
criteria against the policy. Higher taxonomy rank is not an automatic substitute
for an intended performance. Candidate mastery thresholds must match the policy.
Objective statement spans and attached source citations must resolve.

Teaching links must point to inspected explanation/worked-example events in
suitable segments and exercise the required criteria and category. A topic mention,
practice label, objective title, assessment question or isolated concept ID does
not supply explanation credit. Distinct worked-example counts use merged output
spans and normalized text fingerprints: replayed events, span aliases and repeated
text cannot manufacture examples. This is textual deduplication; semantic novelty
and pedagogical adequacy still require contextual assessment.

## BIE-QA-PED-002 — sequence evaluator

Every operator-enumerated route is checked, not only the happy path. Validate
exact route membership, total duration, ordered constraints and minimum spacing.
Use the preserved native iterative graph utility to reject prerequisite and order
cycles. For each route, collect completion times for all required criteria;
prerequisites must be complete before dependent explanatory teaching. Prior
instruction is not measured mastery. Each route needs its own teaching, worked
examples and adequate distinct aligned mastery questions. A diagnostic may
precede teaching but is not counted as mastery evidence.

Only finite, explicit, nonrepeating routes are supported. Arbitrary game state
reachability, branches inferred from executable code, infinite loops, real learner
mastery state and adaptive-path equivalence remain integration obligations. This
is not a complete curriculum optimizer or runtime prerequisite enforcement engine.

## BIE-QA-PED-003 — cognitive-load evaluator

Compute deterministic declared-plan guardrails, not scientific cognitive-capacity
estimates. A half-open sweep line inspects every event boundary and measures peak
simultaneous visual units, motion units and distinct new-concept tags. Touching
intervals do not overlap. Averages cannot hide a short overloaded window.

Count non-whitespace Unicode codepoints from the union of actual referenced text
spans. Check exact rational per-event rates and the sum of concurrent stream
rates against the operator limit. Concurrent identical channels are conservatively
counted as separate presentation demands; no cognitive-theory claim is implied.
A codepoint is not a word, syllable, reading-time estimate or language-independent
unit. Complex-script segmentation and experimentally calibrated pacing remain open.

Also check adjacent distinct-new-concept budgets and uninterrupted presentation
along each route. Only a sufficiently long, content-free break resets the latter.
Actual layouts, camera/motion measurements, captions, narrations, measured audio
length, frame content, interaction latency and learner responses are not inspected.
Those require the later VIS/ANI/AUDIO/VIDEO/GAME checks and EVAL validation.

## BIE-QA-PED-004 — assessment alignment

Require policy-matched cognitive category, response mode, objective criteria,
complete rubric point maxima and inspected prompt, solution, feedback and rubric
text. Transfer requirements cannot be replaced by recall labels. Answers and
feedback must have distinct event roles, a declared response gate and adequate
response time. Reject prompt/answer span reuse, identical answer text and a second
display exposing the same answer during response time. Broader paraphrased leakage
and real gameplay enforcement require contextual and runtime checks.

Every route must contain enough distinct mastery prompts. Repeated item IDs/text,
formative activities and diagnostics cannot inflate this count. A separate
`check_mastery_scores` API recomputes total threshold plus each criterion's hard
minimum using exact integer arithmetic. A high average cannot compensate for a
failed criterion. This API computes a score decision; it never claims an actual
learner was observed, fairly assessed or has mastered the topic.

## Reports, determinism and release connection

Each original task receives a deterministic existing Source Report contract,
findings with owner/detail/severity, measurements, inspected artifact IDs,
request/policy/evidence digests, explicit time and limitations. Result status is
BLOCKED, REVIEW_REQUIRED or CHECKS_PASSED. Product acceptance is always false.
`verify_reports` recomputes, rather than trusting an edited result flag.

The bridge prepares actual report bytes, their hash and an unsigned GateEvidence
for `pedagogical_correctness`, binding the candidate and source inventory.
Blocked local evidence yields FAIL; healthy or review-only plans yield NOT_RUN for
the complete media gate. It never emits PASS and never signs its own evidence.
The existing ReleaseEvaluator is executed in tests and blocks the resulting
incomplete unsigned bundle.

## Bounds and verification

Contracts cap 128 objectives, 256 segments, 1,024 events, 32 finite routes,
1,024 teaching links, 512 assessment items, criterion counts, link counts, total
text work and timing ranges. JSON decoding and CLI input sizes are bounded.
These are safeguards, not proof of production throughput or OS-level isolation.

Six pinned native PED files are preserved and exercised through adapters. The
connector-returned text was reconstructed in the container and verified against
connector-returned Git blob IDs, SHA-256 and byte lengths. Dependencies are
verify-only at integration; never overwrite a newer canonical version with these
snapshots. Their native PASS fields cannot authorize semantic or release success.

Executed evidence: 193 new tests, 1,140 subcases already inside those tests;
prior suites 276/217/134/146/132/10 separately; 20 selected safeguard-removal probes;
three structural JSON schemas; authored synthetic offline demonstration; source
preservation. See the machine receipts for exact test identities and hashes.
Fresh ZIP extraction, manifest checks, reruns, corruption rejection, reconstruction
and master-backup verification are recorded separately in the delivery receipt.

## Acceptance and next work

Bounded local implementation only. Full-section audit, hardening, re-audit,
current-HEAD compatibility, canonical caller adoption, full repository regression,
actual media/game checks, independent assessor calibration, real-learner evidence
and real-book end-to-end acceptance remain open. Next original tasks are
BIE-QA-DIR-001–004. No new hardening IDs are invented in this batch.
