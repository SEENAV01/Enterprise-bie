# Section 16 Batch 004 — prerequisite and reasoning QA

## Authority and scope

Original registry page 17: BIE-QA-PR-001; BIE-QA-RE-001; BIE-QA-RE-002;
BIE-QA-RE-003. Local additive namespace: `bie.qa.reasoning_v2`.
The user has delegated Section 15 to another work session. This package neither
modifies that lane nor infers its completion. No GitHub or global task-state writes.

The BIE product remains a source-grounded, accurate, cinematic and engaging learning
experience with meaningful educational games. These evaluators protect prerequisite,
reasoning and uncertainty quality; they do not certify cinematic quality, learning
outcomes, rendered frames, speech or a playable game.

## Interfaces and result boundaries

`evaluate(request, artifact_root, policy, *, as_of, reviews=(), verifier=None,
source_assessments=(), source_verifier=None)` returns a `ReasoningResult` with
`source`, `prerequisite`, `validity`, `evidence`, `uncertainty`, and explicit witnesses.
Each report binds request/policy/evidence digests and evaluated time. `verify_reports`
recomputes the result and rejects edited or stale supplied reports.

Operator policy is independently supplied. It owns required concepts/arguments,
prerequisite graph, source lineage, learner scope and thresholds. It is not generated
by the candidate being judged. Default keys are empty and cannot approve assessments.
A source-grounding failure propagates rather than being replaced by a caller's PASS.

Statuses are CHECKS_PASSED, REVIEW_REQUIRED, BLOCKED. CHECKS_PASSED is limited to the
declared typed/text evaluation contract. It is not a product-success status.
`product_accepted` always remains false. The optional release-v2 bridge recomputes
results and creates unsigned report bytes/envelopes. Its full source/video/game gates
remain NOT_RUN on healthy text-only evidence, or FAIL on the relevant failed checks.

## BIE-QA-PR-001 — prerequisite evaluator

Reuse the actual pinned PR graph implementation. Require an acyclic policy graph;
never silently remove edges to get a green result. Check that targets appear in the
reviewed schedule and learning events bind real output claims. Validate direct and
transitive prerequisites before each dependent event. Later instruction/diagnostic
availability cannot satisfy an earlier event. Teach/bridge credit requires adequate
explaining depth plus an authenticated teaching judgment; mentions, prompt labels and
questions alone are not teaching evidence.

Rules explicitly choose instruction_or_mastery or mastery_required. Prior instruction
is not measured mastery. Diagnostic credit checks real artifact bytes, learner/concept,
raw correct/total counts, timestamps, lifetime, availability and authorized grading/
provenance review. A newer low diagnostic is not bypassed by selecting an older high
score; equally recent observations use the conservative minimum. Assessor quality and
whether a diagnostic genuinely measures the prerequisite remain external obligations.
A readiness witness identifies the rule/event and prior instruction or observation.
Graph traversal limits block incomplete scans.

## BIE-QA-RE-001 — reasoning validity evaluator

Inputs explicitly bind statements to source-checked output claims, scope, expressions,
root premises, assumptions, inference steps and the final conclusion. Missing steps,
orphans, out-of-scope references, duplicated producers, circular support and irrelevant
proof padding block the relevant check. A declared root cannot also be its own derived
conclusion. Asserted premises/conclusions cannot hide behind nonfactual text labels.
Conditional assumptions require a visible, reviewed conditional conclusion.

Deductive checks are bounded propositional truth-table entailment, supporting atom,
not, and, or, implies and iff. They emit a counterexample assignment when implication
fails. Inconsistent premises do not earn a vacuous PASS. All roots are checked for
consistency, even where one local step could appear valid. Resource exhaustion cannot
promote partial enumeration into proof. Formal truth and premise truth are distinct:
validity is conditional on reviewed normalization and scope. Natural-language parsing,
quantifiers, numerical/algebraic proof and universal domain reasoning are not supplied
by this checker. Math is the next original registry scope.

Causal, inductive, analogical and empirical steps require their own authenticated
assessment. They are labeled REVIEWED_NONDEDUCTIVE, never falsely labeled ENTAILED.
A complete output-to-proof mapping/inventory review remains mandatory.

## BIE-QA-RE-002 — evidence sufficiency

Require premise-by-premise supporting evidence, not a global confidence score or a
large bibliography. Links must resolve real source citations actually attached to the
premise; only authorized contextual-support judgments earn credit. A conclusion cannot
be its own premise evidence, and a declared assumption is not empirical support.

Corroboration is counted by operator-governed source lineage, unioned with identical
source-byte hashes. Repeating citations or relabeling the same bytes does not add an
independent source. Hidden shared ancestry cannot be discovered automatically.
Current reviewed contradictory evidence is a blocker, not a minority vote to ignore.
Witnesses list independent source groups for every premise, with separate assumption
status. Source-grounding checks are rerun on artifact bytes.

## BIE-QA-RE-003 — uncertainty evaluator

Require one disposition for every argument. Calibrations bind artifact bytes, model
identity/version, domain, language, dataset and issue time. The payload must declare
heldout split, distinct sample/group IDs and source hashes. Reject overlap with current
candidate source hashes, duplicate groups, wrong labels/types and weak sample coverage.
These structural checks cannot independently prove genuine holdout or correct labels;
reviewed provenance and applicability are mandatory and remain an operational gap.

Compute 10-bin expected calibration error and Brier error from integer ppm predictions
and Boolean labels. ECE_ppm = ceil(sum_bins(abs(sum_prediction_ppm - correct*1e6))/N).
Brier_ppm = ceil(sum((prediction_ppm - label*1e6)^2)/(N*1e6)). Error rounding is conservative.
The confidence bin must meet its sample floor; published confidence cannot exceed its
observed accuracy floor. These are descriptive empirical diagnostics and configurable
engineering safeguards, NOT a statistical confidence interval or proof of future
accuracy. The actual preserved calibration diagnostics are also executed for compatibility.
Finite labels cannot establish absolute empirical certainty.

Proof/evidence failure requires abstention; unresolved assessments or missing applicable
calibration require review. An optimistic disposition is rejected even when its supplied
confidence is high. Review/abstention/conditional assumptions require evidence of visible
output disclosure. Correct abstention remains an open review, not release acceptance.
The preserved structured-uncertainty contract runs on assurance flags, not multiplied
probabilities. No live provider, learner assessment or held-out real-book calibration ran.

## Authentication and filesystem boundaries

Review HMAC signing domain: BIE-QA-PR-RE-REVIEW-V1 plus NUL and canonical payload bytes.
Bind exact request, policy, subject/purpose, evidence inventory, evaluator/version,
issued/expiry times and rationale. Unknown, revoked, stale, test-only or unauthorized
keys cannot approve operational evidence. Principal/key independence is configured
outside the candidate; the same secret cannot be relabeled as independent voters.
Any current authorized rejection or uncertainty prevents positive-vote promotion.
Authentication does not establish reviewer correctness or actual independence.
No runtime signer, production secret, outbound execution or network client is included.

Read source and supporting artifacts using the inherited bounded snapshot reader.
Hash, size, path confinement, unsafe filesystem objects and hardlinks are checked.
Reports verify bytes at evaluation time, not future mutable publication bytes.
The CLI does not load keys and refuses to overwrite an existing output file.

## Structural and computational limits

Three closed structural JSON schemas accompany request, policy and review. They reject
unknown fields and malformed expressions but do not replace runtime codecs, graph,
freshness, identity, trust or semantic checks. Runtime codecs reject floats where integer
ppm is required, duplicate JSON keys and malformed collections. Resource caps include
12 proof atoms, expression depth 16 and 127 nodes/expression; at most 128 arguments,
1,024 learning events and steps, 256 mastery artifacts, 16 calibration artifacts;
64 MiB aggregate referenced bytes and 4 MiB per supporting artifact. Policy narrows
truth assignments, graph checks and node visits. No eval of untrusted expressions.

## Verification and integration obligations

Run the new verifier, then preserve its nested parent receipts. Read the executed
TEST_RESULT.json for actual counts; subcases, replays and shared atomic ZIPs are not
additional tests. Selected fault-removal probes require a passing control, valid mutated
syntax and an assertion failure, not an import error. They are not exhaustive mutation
coverage or a full security audit.

At section adoption re-read the current repository HEAD, conflict-check additive code,
verify native dependency bytes or migrate explicitly, run the full canonical suite and
live operator/provider integration, obtain actual media/game/real-book evidence, and
perform section audit/hardening/re-audit. Do not overlay frozen dependency snapshots on
newer repository files. Final acceptance remains downstream.
