# BIE-COMP-H10-003 — Required action realization instead of registry-only availability

## Existing finding and baseline

Derived from H3-R02. H9 static_focus requirement passes with zero animation tracks.

Parent: H9-005, SHA256 295628ff2a5d076117a6e87aad66536962a32f7beb28c43673390fe2017e5d4e.

## Contracts and implementation

See `docs/comp_h10/CONTRACTS.md` and the task registry. Contract changes are explicit;
legacy fixtures and source are not recreated. All four ordered deltas must be
restored before test execution; intermediate stages are source-assembly states.

## Executable tests

```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h10_003 -v
```

Negative tests and source/target/provenance identity checks are included. Test
execution results are in the adjacent TASK_RESULT.json and TEST_RESULT.txt.

## Acceptance boundaries

Implemented local contracts are not whole-section or product acceptance. API-double
and actual-runtime evidence must remain separate. No GitHub write is included.
