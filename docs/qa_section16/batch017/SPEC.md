# Section 16 Batch 017 — regression and diffs

## Authority and scope
Original registry page 18, BIE-QA-REG-001..005. Additive namespace
`bie/qa/regression_v2`. The original 76-entry registry is the baseline, not a
completion ceiling. This package is cumulative Section16, not the full repository.
Section15 remains externally managed. No canonical code, global task continuation,
Codex/Android files or GitHub resources are edited.

## Data contract and trust
`RegressionRequest` names baseline/candidate `repair_v2.Snapshot` records and an
external execution `ArtifactRef`; `RegressionPolicy` is operator-owned, not
candidate-provided. The same artifact ID can have distinct old/new bytes; actual
references and both snapshot digests are bound to the comparison. Separate roots
are mandatory. Source SnapshotStore reads real bytes with hashes, sizes, bounded
read budgets and no-follow file descriptors. Complete snapshot inventories reject
extra files, links and nonregular entries. Immutable operator-owned roots are still
a deployment requirement, including parent-path and concurrent-write trust.

Wire JSON is data-only, integer-based and duplicate-key rejecting. Constructors
and evaluator validate relationships beyond the three structural JSON schemas.
No test functions, shell commands, network providers or trusted keys are selected
by request JSON. Registered top-level Python callbacks come from the operator.

Fresh purpose-scoped reviews cover the exact comparison inventory, execution record
and each typed semantic record's interpretation. Missing, stale, test-only,
rejected, uncertain, mismatched or revoked review cannot authorize a pass. A signed
approval does not override failed comparisons. Test helpers contain conspicuously
SYNTHETIC credentials to exercise successful authentication; they are never runtime
trust defaults. Authentication is not scientific correctness or evaluator calibration.

## REG-001: regression suite
`collect()` checks protected fixture identities, pins each validator's function and
defining module, then executes two POSIX resource-bounded processes on separate
private copies. Exact required check/case IDs and fixtures must be returned.
Exceptions, timeout, incomplete observations and mutation of private inputs are
recorded as failure. Source snapshots are rechecked before and after execution.

`evaluate()` independently rereads the execution bytes and validates bindings,
freshness, environment hash, process outcome, independent execution IDs, phase
order and case coverage. Each required candidate case must PASS; a prior PASS may
not regress. Baseline FAIL can be a repaired defect, but baseline NOT_RUN/REVIEW/
ERROR cannot establish a valid comparison. No average score, empty collection,
last-success retry or count-only receipt grants acceptance.

Callback/module pinning does not independently enumerate transitive imports.
POSIX limits are not an adversarial-code sandbox or a distributed executor.
The explicitly enumerated registry is not automatically a complete canonical suite.

## REG-002: artifact diff
Both entire inventories are read, including unchanged and protected bytes.
Adds, removals, content, path and role changes are reported by stable artifact ID.
Every nonprotected change requires an operator-supplied ChangePermit binding the
complete before/after ArtifactRef digests and a reason. Protected changes and
unused or stale permits block. Permits are change-scope authorization, not evidence
that the new content is correct. No changed file is inferred to be a harmless rename.

## REG-003: typed semantic diff
Supported `bie.qa.semantic-snapshot/1` JSON contains `concept_ids`, claims and
relations. Claims include stable `claim_id`, `concept_id`, literal `text`,
`source_refs`, `conditions`, an opaque `expression`, support `status` and integer
`confidence_ppm`. Relations have `from`, `predicate`, `to`.

Required concepts/claims must exist in both snapshots. Lost conditions, source
references, relations, and explicit contradiction block. Changed wording,
expressions, confidence or graph structure require review; no embeddings or lexical
similarity are used to assert equivalence. Reordered claim inventory is not a
meaning change. Source reference IDs are inspected typed mappings, not an automatic
replacement for native source-anchor verification. The inherited source/semantic
QA gates remain necessary. No live model, natural-language entailment, universal
factual evaluator or automatic canonical KI exporter is established here.

## REG-004: visual diff
Reads actual single-frame RGB/RGBA/L/LA PNG bytes. Exact operator-specified dimensions
and sample identities are required; no rescaling, registration, pixel dropping or
candidate-chosen masks. Reports RGBA channel deltas, changed fraction, changed bbox,
masked pixels and critical-region changes. Integer cross-multiplication prevents
rounding the changed fraction into a pass. A critical pixel change cannot be hidden
by a small global average or a channel tolerance. Alpha and hidden RGB are included.

Explicit operator mask regions have a conservative sum-area cap and cannot overlap
critical regions. Profiles/gamma/EXIF/transparent-color metadata require review.
Limits: 2,097,152 pixels per pair, 8,388,608 total specified comparison pixels,
32 masks/critical regions per pair. These are declared PNG samples, not complete
video comparison, arbitrary occlusion semantics or cinematic quality ratings.

## REG-005: game-state diff
Reads `bie.qa.game-traces/1` JSON with finite runs (`scenario_id`, `seed`,
`execution_mode`, `steps`). Each step has exact `action_id`, `input`, `state`,
`score`, `feedback`, `terminal`, `enabled_actions`. Policy `Scenario` controls
required action sequence, seed and initial INIT step; missing/duplicate/reordered
scenarios or checkpoints block. Every state field is compared without numerical
coercion or ignore lists. Boolean true is not numeric one. Scores, feedback, hidden
state and enabled controls cannot be omitted. Equal traces do not prove rule
correctness, learning, all possible branches or native browser execution. NODE_REDUCER,
REPORTED and SYNTHETIC modes remain review-required. An OBSERVED_BROWSER label is
not independently trusted; provenance is part of the fresh inventory review.

## Release bridge
`prepare_release_evidence()` reruns evaluation, binds candidate bytes and emits
unsigned FAIL for blocked checks or NOT_RUN otherwise. Never full-regression PASS.
All final source/video/game/benchmark/real-book release gates remain required.

## Reproducible local usage
From an extracted package with Python, Pillow and jsonschema available:

    python -B scripts/verify_qa_regression16_batch017.py --output /tmp/new-qa17-tests
    python -B scripts/demo_qa_regression16.py --output /tmp/new-qa17-demo
    python -B scripts/recheck_qa_regression16_diagnostics.py /tmp/new-qa17-demo

The demo also needs installed Node. Its callbacks/approvals/lesson are authored
technical fixtures, not native Section15 or real-book learning output. Replay of
stored reports is a recomputation, not a new worker execution.

Read-only unsigned CLI (must use a new output path outside input trees):

    python -B -m bie.qa.regression_v2 --request request.json --policy policy.json \
      --baseline-root baseline --candidate-root candidate --evidence-root evidence \
      --as-of 1801000000 --output new-result.json

Exit 0: bounded checks passed; 2: blocked; 3: review required; 4: contract/IO failure.
The CLI provisions no keys and imports no callbacks from JSON.

## Acceptance and next work
Actual new and inherited tests, fault-injection probes, authored execution diagnostics,
preservation, extraction and corruption checks are required for this local package.
Section exit still requires enterprise-completeness audit, justified hardening and
re-audit. Canonical adoption/full regression, broad stream/video/game comparison,
production isolation and real-book E2E remain open. Next registry entries are
BIE-QA-REPRO-001..003 (deterministic rerun, environment reproduction, artifact hashes).
