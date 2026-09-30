# BIE-APP-GRAPH-001 — concept graph viewer

## Original capability

concept graph viewer

## Implemented Batch 001 scope

Owned implementation files:
- `bie/app_product/contracts.py`
- `bie/app_product/graph_view.py`

Primary verification:
- `tests/section18/test_app_graph_001.py`
- shared canonical-backed fixture support: `tests/section18/support.py`

## Evidence rules

The task must consume canonical BIE runtime/graph state where applicable, remain
deterministic and bounded, reject unsupported states, and avoid fabricated success.
A passing local task is not Section 18 or product acceptance.
