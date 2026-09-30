# BIE-EVAL-RATER-001 — deterministic evaluator

Original registry sequence 42; Section 17 Batch 005.

## Scope and acceptance status

Execute the actual 17 supported metric profiles, bind candidate/reference/rubric/service-code digests, retain detailed metric receipts and blocked failures.

Status: scoped local implementation, NOT complete enterprise capability acceptance.

## Contracts and execution

Runtime implementation: `bie/evaluation/benchmarks/release/deterministic.py`.
Direct task dependencies: BIE-EVAL-METRIC-017. The individual ZIP carries a cumulative runtime dependency closure; it is not a permission to overwrite a native repository.

`EXAMPLE_INPUT.json` is an authored worked example. `EXAMPLE_OUTPUT.json` was produced by the actual public function. The test expectations are declared independently in `test_rater_001.py`. Candidate-owned pass flags are not accepted. Context hashes bind run, case, domain, metric, candidate, reference, rubric, dataset, environment and split. All public scores use bounded exact rational arithmetic. Malformed data raises `BenchmarkError`; evaluator/service boundaries retain explicit BLOCKED receipts where defined.

## Positive, negative and boundary verification

Run from `runtime/` in this atomic package, or `combined_source/` in the master:

```bash
python -B tools/run_section17_batch005_tests.py --pattern test_rater_001.py --output-dir /tmp/BIE-EVAL-RATER-001-new-test-run
```

Use a new output directory. The package retains the selected test names and actual results, negative/missing/duplicate/boundary checks, one targeted implementation-fault control and its restored run, cumulative regression results and fresh-extraction verification. Repeated runs and fixture scenarios are not counted as extra unique test methods.

## Evidence/provenance and security

The original task identity is preserved in `metadata/section17/ORIGINAL_50_TASK_REGISTRY.json`. Authored examples are DEVELOPMENT data, not independently reviewed golden references. See `BATCH005_REFERENCE_CATALOG.json` for implementation references. Digests show content identity, not authenticity. Production verification must protect evaluator code, references, keys and ledger from candidate workers. Test keys and fixture responses confer no external authority.

## Limits and remaining acceptance work

Bounded structured reference profiles; no arbitrary-language or native BIE adapter certification.

No GitHub write/commit, native repository regression, real-book end-to-end acceptance or Task 028 execution is included. Whole-section capability audit, justified hardening and re-audit remain required.
