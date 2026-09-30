# BIE-EVAL-H1-005 — Supervised provider deadline

## Lineage and authority
Derived hardening task H1-F005, after the original50-task local roster. This is not a new original registry task. Section and product acceptance remain false. Baseline master: `89d8eedc87075739c316f308bdc2f777063a9502bd125a21f245f36ca35d0ae4`.

## Finding
The model port delegated timeouts to the adapter; a hanging callback had no enforced process deadline.

## Implemented contract
Offer an operator-installed factory wrapper with spawned worker, bounded UTF-8 response channel, deadline termination and direct-child reaping.

Owned/shared implementation: `bie/evaluation/benchmarks/release/supervised.py`.
Affected original capabilities: BIE-EVAL-RATER-002. Shared gate/ledger changes require the combined H1 runtime, not arbitrary file-by-file overlays.

## Observable acceptance checks
`test_h1_005.py` contains 13 distinct executed test methods. Positive, negative and malformed-input controls are runnable from the atomic runtime. Detailed actual IDs and statuses are in `TEST_RESULT.json`; repeated executions and subtests do not inflate counts. Selected injected-fault sensitivity is recorded separately.

## Run
```sh
python -B tools/run_section17_h1_tests.py --pattern test_h1_005.py --output-dir /tmp/bie-eval-h1-005-new
```
Run from the individual ZIP's `runtime/`, or the master `combined_source/`. Choose a fresh output directory. The atomic runtime includes its required code/data/helpers; it is not an installer or authorization to overwrite the canonical repository.

## Evidence and input/output examples
The exact test file and `tests/section17/h1_helpers.py` / `batch005_helpers.py` are executable input/output examples. Keys and production-mode control inputs in these helpers are SYNTHETIC TEST ONLY. Eight persisted H1 diagnostic scenarios, reservation recovery and the direct-worker timeout receipt are supplied in the combined master. No fixture becomes an independently reviewed reference by changing a label.

## Explicit remaining boundary
Not an OS sandbox: descendant, network, memory, service authorization and provider billing cancellation remain deployment concerns. Wrapper adoption by the native broker is not automatic.

## Integration and rollback
Review `metadata/section17/H1_CHANGE_LEDGER.json` before replacement. Existing-code preimages and baseline SHA256 values are retained. Keep candidate/reference/trust stores separate. Do not downgrade live hardened data to an older schema by replaying old atomics. No GitHub write or Task028 update is authorized by this task.
