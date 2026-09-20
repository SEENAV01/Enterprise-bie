# BIE-COMP-H8-001 — Full-raster contribution and connected-ink analysis

Inherited finding: H3-R01. Parent checkpoint: BIE-COMP-H7-008.

## Implemented contract
Read bounded opaque RGB PNG bytes once with file/hash/profile checks. Inspect all output pixels using isolated-minus-baseline and full-minus-muted contribution; report all connected components including small marks. Reject insufficient contribution, lost components, unexpected hidden paint and unresolved required ink. Byte/pixel/run limits block rather than sampling. This is a target-contribution diagnostic, not OCR, semantic image understanding or acceptance.

## Files
- `app/bie/compiler/raster_ink.py`
- `tests/compiler/h8_test_support.py`
- `tests/compiler/test_comp_h8_001.py`

## Verification
38 task tests passed; shared cross-task integration has 18 tests. Restore all five H8 source deltas before running task suites. These results are local technical evidence, not product acceptance.

## Run
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h8_001 -v
```
