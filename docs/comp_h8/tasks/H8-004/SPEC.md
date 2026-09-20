# BIE-COMP-H8-004 — Finite live DSL-to-consumer coverage reconciliation

Inherited finding: H3-R02. Parent checkpoint: BIE-COMP-H7-008.

## Implemented contract
Inventory the live registry and actual dispatch functions, record source identities and reproduce missing names. It observes 18 element types/16 actions, 15 element emitter entries and 9 supported action names. Missing shape/diagram/highlight and seven action names remain explicit implementation/lowering gaps. Source dispatch presence does not certify all properties/combinations. A forged or stale PASS is rejected. This task is a coverage diagnosis, NOT implementation of missing consumers or a closure verdict.

## Files
- `app/bie/compiler/consumer_coverage.py`
- `scripts/inspect_comp_coverage.py`
- `tests/compiler/test_comp_h8_004.py`

## Verification
19 task tests passed; shared cross-task integration has 18 tests. Restore all five H8 source deltas before running task suites. These results are local technical evidence, not product acceptance.

## Run
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h8_004 -v
```
