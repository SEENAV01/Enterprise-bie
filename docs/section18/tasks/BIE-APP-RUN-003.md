# BIE-APP-RUN-003 — source validation UI

## Original capability

source validation UI

## Implemented Batch 001 scope

Owned implementation files:
- `bie/app_product/contracts.py`
- `bie/app_product/source_validation.py`

Primary verification:
- `tests/section18/test_app_run_003.py`
- shared canonical-backed fixture support: `tests/section18/support.py`

## Evidence rules

The task must consume canonical BIE runtime/graph state where applicable, remain
deterministic and bounded, reject unsupported states, and avoid fabricated success.
A passing local task is not Section 18 or product acceptance.
