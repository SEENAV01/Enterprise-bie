# BIE-EVAL-H1-009 — Durable finalization and explicit recovery

## Lineage and authority
Derived hardening task H1-F009, after the original50-task local roster. This is not a new original registry task. Section and product acceptance remain false. Baseline master: `89d8eedc87075739c316f308bdc2f777063a9502bd125a21f245f36ca35d0ae4`.

## Finding
A finalization could return a receipt without ensuring its reserved row was finalized; interrupted reservations lacked a governed terminal recovery path.

## Implemented contract
Compare-and-set finalization, read-back integrity, artifact/report bindings and explicit input-pinned operator recovery to terminal BLOCKED.

Owned/shared implementation: `bie/evaluation/benchmarks/release/ledger.py`.
Affected original capabilities: BIE-EVAL-REL-004. Shared gate/ledger changes require the combined H1 runtime, not arbitrary file-by-file overlays.

## Observable acceptance checks
`test_h1_009.py` contains 13 distinct executed test methods. Positive, negative and malformed-input controls are runnable from the atomic runtime. Detailed actual IDs and statuses are in `TEST_RESULT.json`; repeated executions and subtests do not inflate counts. Selected injected-fault sensitivity is recorded separately.

## Run
```sh
python -B tools/run_section17_h1_tests.py --pattern test_h1_009.py --output-dir /tmp/bie-eval-h1-009-new
```
Run from the individual ZIP's `runtime/`, or the master `combined_source/`. Choose a fresh output directory. The atomic runtime includes its required code/data/helpers; it is not an installer or authorization to overwrite the canonical repository.

## Evidence and input/output examples
The exact test file and `tests/section17/h1_helpers.py` / `batch005_helpers.py` are executable input/output examples. Keys and production-mode control inputs in these helpers are SYNTHETIC TEST ONLY. Eight persisted H1 diagnostic scenarios, reservation recovery and the direct-worker timeout receipt are supplied in the combined master. No fixture becomes an independently reviewed reference by changing a label.

## Explicit remaining boundary
Single-host privileged recovery requires stopping the abandoned worker first. It is not an authenticated public recovery endpoint or distributed crash reconciliation. Pre-H1 finalized receipts require explicit revalidation; do not rewrite archived evidence.

## Integration and rollback
Review `metadata/section17/H1_CHANGE_LEDGER.json` before replacement. Existing-code preimages and baseline SHA256 values are retained. Keep candidate/reference/trust stores separate. Do not downgrade live hardened data to an older schema by replaying old atomics. No GitHub write or Task028 update is authorized by this task.
