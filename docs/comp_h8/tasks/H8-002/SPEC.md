# BIE-COMP-H8-002 — Projected map feature resolution and ambiguity

Inherited finding: H3-R01. Parent checkpoint: BIE-COMP-H7-008.

## Implemented contract
Consume exact existing source layer IDs and full-resolution pixel masks for point, route and polygon features. Detect absent/small/collapsed geometry, inseparable points and mostly coincident routes with explicit pixel policies. Preserve every source coordinate, layer and provenance; no inferred basemap, geographic truth assertion or automatic feature deletion. Distinct crossings and owners are not conflated.

## Files
- `app/bie/compiler/cartographic_qa.py`
- `tests/compiler/test_comp_h8_002.py`

## Verification
29 task tests passed; shared cross-task integration has 18 tests. Restore all five H8 source deltas before running task suites. These results are local technical evidence, not product acceptance.

## Run
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h8_002 -v
```
