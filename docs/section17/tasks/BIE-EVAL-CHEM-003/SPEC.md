# BIE-EVAL-CHEM-003 — stoichiometry

## Original scope and actual local status
Section 17 original sequence **16** of 50; Batch002. **SCOPED_LOCAL_IMPLEMENTATION_VERIFIED. Original capability NOT fully closed.** This is a continuation of Batch001, not an engine replacement or an enterprise acceptance certificate.

## Observable implementation
Unique positive balancing with charge conservation, limiting feeds and molar yield.

## Explicit domain limits
<=6 reactants and <=6 products, bounded 118-element formula grammar, parentheses/brackets depth<=4, <=128 formula characters, per-element count and coefficients<=10000. Nullity-one strictly positive primitive balance only. Explicit charge, complete feeds and full coefficient roster. Hydrates/isotopes/phase/charge-suffix notation and underdetermined ratios are refused, not guessed. No mass-to-mole/atomic-weight database or reaction-feasibility proof.

## Operations and defect-specific fixtures
| Operation | Authored case identities |
|---|---|
| `balance` | BIE-EVAL-CHEM-003.C001, BIE-EVAL-CHEM-003.C002, BIE-EVAL-CHEM-003.C003, BIE-EVAL-CHEM-003.C009, BIE-EVAL-CHEM-003.C010, BIE-EVAL-CHEM-003.C012 |
| `reaction_extent` | BIE-EVAL-CHEM-003.C004, BIE-EVAL-CHEM-003.C005, BIE-EVAL-CHEM-003.C006, BIE-EVAL-CHEM-003.C011 |
| `percent_yield` | BIE-EVAL-CHEM-003.C007, BIE-EVAL-CHEM-003.C008 |

The sibling `CONTRACT_EXAMPLES.json` provides concrete exact input/output records and separately authored derivations. The implementation is `bie/evaluation/benchmarks/domains/stoichiometry.py`. Its `solve(data)` accepts a typed JSON object with an explicit operation, rejects unknown/missing fields and unsupported profiles, and never executes input as code. `runner.reference_output(task_id, inputs)` produces `{"status":"OK","values":...}` or `{"status":"REJECTED","error_code":"..."}`. Unexpected runtime defects propagate rather than masquerading as academic rejection. Rejections do not count as implementation of the refused profile.

Numeric ratios are exact rational strings unless the documented contract uses integer counts. Canonical JSON rejects non-finite values, arbitrary Python objects and oversized/deep input; booleans are not quantities. Unit conversion is explicit. Comparison is schema-exact and preserves claim/evidence types rather than scoring word overlap. No network fetch, provider call, filesystem path supplied by the candidate, interpreter or shell invocation is involved in these reference functions.

## Evidence and reference custody
Twelve original authored diagnostic problems are versioned as DEVELOPMENT / AUTHORED_DIAGNOSTIC, with case identity, source records, derivation, leakage family and exact expected result. Public examples are not a hidden test set. Source links in `metadata/section17/BATCH002_REFERENCE_CATALOG.json` identify material reviewed for the declared model; they are not retrieved page spans, source-content rights grants or independent reviewer approvals. Fixed prose/annotation profiles are not general NLP entailment.

The existing registry, immutable dataset snapshots, attempt ledger and structured grade path are reused. Public candidate views omit expected answers and derivations. Production reference isolation must be provided by native infrastructure, not by giving the candidate this private evaluator directory. Missing answers remain in the frozen denominator, and caller-supplied pass flags cannot authorize release.

## Tests actually run
The selected task suite has **22 distinct methods**: 12 separately authored fixture replays plus 10 additional invariance, boundary, negative or scope tests. Each method may exercise several subcases; those are NOT additional methods. This suite is a subset of the 493-method cumulative run, not an extra 22 passes. Exact method IDs and actual outcomes are in `metadata/section17/tasks/BIE-EVAL-CHEM-003/TEST_RESULT.json` and `TEST_RESULT.txt`. The cumulative suite also exercises CLI, persistence, anti-gaming, source records, original-file preservation, strict grading and safe package extraction. Eight separate in-memory fault controls are recorded without adding repeat executions to the method count.

From the consolidated candidate directory:
```bash
python -B tools/run_section17_tests.py --pattern test_chem_003.py --output-dir ../BIE-EVAL-CHEM-003-test-new
```
Use a new output directory outside the candidate. The master archive additionally contains actual fresh-extraction verification for this task's self-contained atomic ZIP. This is local Python verification, not a live BIE source/video/game benchmark.

## Owned paths and dependencies
Direct dependencies: BIE-EVAL-CHEM-001. Shared Batch002 runtime support is accounted for, not attributed as ten separate new implementations.

- `bie/evaluation/benchmarks/domains/stoichiometry.py`
- `bie/evaluation/benchmarks/data/BIE-EVAL-CHEM-003.json`
- `tests/section17/test_chem_003.py`

## Packaging, audit and continuation
Atomic ZIPs include the owned delta and a pinned shared runtime for independent selected-task execution. The runtime is a dependency snapshot, not this task's owned payload and not a full BIE app. `OWNERSHIP.json` distinguishes the two. Use `combined_source/` in the master package for a ready-assembled checkpoint; never overlay an atomic runtime or the full master onto GitHub main.

Prior Batch001 artifacts, logs and hashes remain preserved. Source changes are enumerated in the change ledger. Read the batch audit, gap ledger and current continuation before the next task. No canonical file, GitHub branch, commit, global continuation or Task028 lane is changed by this delivery.

Independent subject/source review, golden/held-out corpora, calibrated rubrics, native adapters, exact canonical regression, downstream metrics/raters/release gates and real-book E2E remain open. Passing reference fixtures does not measure cinematic quality, complete subject coverage, pedagogy or learning improvement.
