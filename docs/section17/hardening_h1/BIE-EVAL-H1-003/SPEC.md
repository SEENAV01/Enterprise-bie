# BIE-EVAL-H1-003 — Deterministic execution and result boundary

## Lineage and authority
Derived hardening task H1-F003, after the original50-task local roster. This is not a new original registry task. Section and product acceptance remain false. Baseline master: `89d8eedc87075739c316f308bdc2f777063a9502bd125a21f245f36ca35d0ae4`.

## Finding
Unexpected metric errors escaped; a malformed/misbound/overcredited result could escape or be represented incorrectly.

## Implemented contract
Freeze evaluator inputs; validate context pins, unit-weighted scores and receipt construction inside one fail-closed boundary; redact exception details.

Owned/shared implementation: `bie/evaluation/benchmarks/release/deterministic.py`.
Affected original capabilities: BIE-EVAL-RATER-001. Shared gate/ledger changes require the combined H1 runtime, not arbitrary file-by-file overlays.

## Observable acceptance checks
`test_h1_003.py` contains 18 distinct executed test methods. Positive, negative and malformed-input controls are runnable from the atomic runtime. Detailed actual IDs and statuses are in `TEST_RESULT.json`; repeated executions and subtests do not inflate counts. Selected injected-fault sensitivity is recorded separately.

## Run
```sh
python -B tools/run_section17_h1_tests.py --pattern test_h1_003.py --output-dir /tmp/bie-eval-h1-003-new
```
Run from the individual ZIP's `runtime/`, or the master `combined_source/`. Choose a fresh output directory. The atomic runtime includes its required code/data/helpers; it is not an installer or authorization to overwrite the canonical repository.

## Evidence and input/output examples
The exact test file and `tests/section17/h1_helpers.py` / `batch005_helpers.py` are executable input/output examples. Keys and production-mode control inputs in these helpers are SYNTHETIC TEST ONLY. Eight persisted H1 diagnostic scenarios, reservation recovery and the direct-worker timeout receipt are supplied in the combined master. No fixture becomes an independently reviewed reference by changing a label.

## Explicit remaining boundary
Bounded deterministic profiles still do not judge arbitrary language or guarantee scientific truth. Re-audit malformed-result failures and fixes are retained.

## Integration and rollback
Review `metadata/section17/H1_CHANGE_LEDGER.json` before replacement. Existing-code preimages and baseline SHA256 values are retained. Keep candidate/reference/trust stores separate. Do not downgrade live hardened data to an older schema by replaying old atomics. No GitHub write or Task028 update is authorized by this task.
