# BIE-APP-RUN-007 — retry controls

## Original capability

retry controls

## Implemented Batch 001 scope

Owned implementation files:
- `bie/app_product/contracts.py`
- `bie/app_product/operator_store.py`
- `bie/app_product/service.py`

Primary verification:
- `tests/section18/test_app_run_007.py`
- shared canonical-backed fixture support: `tests/section18/support.py`

## Evidence rules

The task must consume canonical BIE runtime/graph state where applicable, remain
deterministic and bounded, reject unsupported states, and avoid fabricated success.
A passing local task is not Section 18 or product acceptance.

## Retry immutability rule

A retry does not overwrite the failed run's immutable result/evidence identifiers.
It creates a new canonical child job using the exact CAS-bound source bytes, records
a durable parent→child retry link, and leaves the failed parent/evidence intact.
A second retry is rejected while the latest child is READY/RUNNING/SUCCEEDED.
