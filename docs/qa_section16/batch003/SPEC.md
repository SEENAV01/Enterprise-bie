# Section 16 Batch 003 — SEM evaluator specification

Original registry page 17: BIE-QA-SEM-001 factual evaluator; BIE-QA-SEM-002
concept-coverage evaluator; BIE-QA-SEM-003 contradiction evaluator. This batch
continues Batches 001–002 under `bie/qa/semantic_v2`; it does not replace them.

## Product purpose and boundary

BIE must turn source-grounded knowledge into understandable, accurate, engaging
educational video and meaningful learning games. Cinematic polish cannot excuse
incorrect facts, missing core explanations or inconsistent feedback. These checks
are one component of that product, not evidence that cinematic or learning quality
has already been achieved. Section 15 is owned by the user's other work session;
its completion is not a prerequisite to this local QA development lane.

## Executable behavior

### SEM-001 — factual evaluation

Recompute Batch002 source/provenance checks from actual artifact bytes. Require
complete, authorized normalization for each factual claim and authorized review
of each reference fact. The operator owns the expected reference IDs, approved
source IDs, predicate semantics, context keys, freshness and confidence floors.
For reviewed atoms, compare exact symbol values/polarity and closed numerical
intervals. A cited reference must entail the candidate; mere range overlap is
insufficient. A [4,6] reference does not establish a precise value of 5. A precise
5 can establish the weaker [4,6] proposition under the same explicit scope.

No unit conversion, omitted condition, missing time scope, alternative scenario,
uncited fact, reported confidence, or positive judgment silently makes an
unsupported proposition correct. Conflicting reviewed reference facts block;
there is no majority-source override. Different contexts abstain rather than
silently treating a conditional statement as universal. This is reference-relative
factual checking, not an unrestricted current-world truth oracle.

### SEM-002 — concept-coverage evaluation

The operator supplies required concept facets, teaching depth, allowed text
channels, weights and critical flags. Links bind real output claims and require
established factual support plus an authorized alignment/depth assessment. The
local rubric is 1 mention, 2 explain, 3 apply, 4 derive; it is a design rubric, not
an independently validated external pedagogical scale. Requirements have a
minimum depth of 2. Merely naming a concept, reusing its ID or asserting a depth
cannot earn credit. Duplicate/alternative links count a requirement only once.
Weighted coverage uses exact integer arithmetic; a missed critical facet blocks
even above the weighted threshold. Unsupported/contradictory teaching is not
accepted as complete coverage. The completeness of the operator's requirement
inventory and the educational adequacy of the depth assessment still need EVAL.

### SEM-003 — contradiction evaluation

Compare normalized atoms within a claim and across all declared text channels.
Governed single-valued predicates can conflict on differing positive values;
multi-valued predicates do not. Explicit positive/negative assertions on the same
symbol conflict; different negative alternatives are not assumed exclusive.
Closed disjoint quantity ranges conflict. Different entities/contexts are not
conflated. Unauthenticated normalized conflicts are review candidates, not proof
that the actual text contradicts itself. Positive consistency judgments cannot
override a detected reviewed conflict.

An authorized complete-scope consistency assessment remains required for semantic
contradictions outside this deliberately small typed grammar. No typed conflict
found is NOT a claim that arbitrary natural-language output is consistent.

## Trust and identity

The source and semantic verifier configurations are independent and default to
empty/deny-all. Wire requests contain no trust keys and cannot configure policy.
Every assessment binds the full request digest, full operator-policy digest,
purpose, subject, exact citation set, evaluator identity/version and validity
interval. HMAC authentication uses a distinct SEM domain prefix. It is local
shared-secret authentication, not remote attestation or proof of correctness.
Test-only credentials cannot promote results to operational support.

Assessment IDs and each evaluator's vote per subject/purpose are unique.
Provisioned independence groups, not key count or number of responses, satisfy
quorum. An evaluator principal cannot be assigned contradictory independence
groups. Rejected, uncertain, unauthenticated or stale evidence is not averaged
away. Authenticity, factual correctness and evaluator calibration remain distinct.

## Interfaces

- `evaluate(request, artifact_root, policy, *, as_of, assessments=(), verifier=None,
  source_assessments=(), source_verifier=None)` returns factual, coverage,
  contradiction and recomputed upstream source reports.
- Focused wrappers expose each task; `verify_reports` reruns the real computation
  and rejects edited/stale results.
- `logic.compare` exposes the conditional typed kernel. It alone cannot accept a
  learning product or establish that a language normalization/reference is true.
- `codec` loads closed-world JSON. `__main__` accepts separately provisioned
  request/policy paths, but never keys from generated input. CLI exit codes are
  0 checks passed, 2 blocked, 3 review required, 64 invalid input/I/O.
- `adapters` actually consumes the preserved canonical KI contradiction detector,
  RE contradiction-resolution validator and DIR lesson validator. Legacy CLEAR,
  resolved flags and planned objective IDs cannot authorize semantic acceptance.
- `bridge.prepare_release_evidence` recomputes checks and returns exact report
  bytes and one unsigned `semantic_correctness` envelope. The canonical gate
  requires source/video/game semantics; text-only success is always NOT_RUN, not
  PASS. Any semantic blocker produces FAIL. It neither publishes nor signs.

## Resource and normalization bounds

Up to 4096 collection records; 64 atoms per normalized claim; 8192 total atoms;
32 explicit context keys; 8192 assessment receipts. Exact decimals permit up to
12 integer digits and 9 fractional digits, with canonical strings and no exponent,
NaN, infinity, negative zero or floating-point coercion. Complete comparison work
is bounded by an operator budget (default 100000, absolute maximum 1000000).
Over-budget scope is rejected before pair scans; no truncated scan passes.
Source/output byte limits and secure POSIX snapshot behavior are inherited from
Batch002. Large-book throughput, memory stress and cross-platform security
acceptance remain separate obligations, not implied by these bounds.

## Evidence and reproducibility

Receipts include executed test IDs and source hashes, inherited regression results,
canonical dependency identities and full parent-file preservation checks. Selected
mutation probes run passing controls and deliberately altered copies. Reports are
stable for the same inputs, policy, keys and explicit clock. ZIP rebuilding from
stored package bytes is verified in this environment; it is not a claim of an
independent operating-system matrix or immutable publication backend.

## Not implemented/accepted by this batch

No live language model, human assessment service, NLP normalizer, calibrated
reference curation service, native PDF/OCR run, real textbook E2E, rendered video,
actual speech, browser game, full-repository regression, canonical caller migration,
production trust backend or production release was executed. Positive provisioned
key cases are clearly synthetic test simulations. Original QA-PR/RE/MATH/PED/DIR/
VIS/ANI/AUDIO/VIDEO/GAME/REPAIR/REG/REPRO/RIGHTS/SEC/PERF/REL work remains governed by
the original registry. Local implementation is not full-task integration or product
acceptance; the cumulative gap ledger preserves every residual obligation.
