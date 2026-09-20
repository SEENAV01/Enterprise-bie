# BIE-COMP-H8-003 — Bound frame-complete counterfactual capture

Inherited finding: H3-R01. Parent checkpoint: BIE-COMP-H7-008.

## Implemented contract
Derive owner/map targets from checked Scene IR, capture all frames and baseline/isolated/muted/full/repeat images, preserve source properties while changing only reversible visibility, and verify source identity, mode coverage, PNG hashes and restored pixels. The local producer is real Chromium with declared React/Remotion doubles. Missing/changed images, fonts, unexpected network calls or unsupported blend/filter attribution cannot become a scoped PASS. Intentional blank caption and zero-alpha frames are source-driven exceptions, not omitted measurements.

## Files
- `app/bie/compiler/raster_capture.py`
- `app/bie/compiler/raster_browser.py`
- `app/bie/compiler/qa_support/raster_modes.js`
- `scripts/verify_comp_raster.py`
- `tests/compiler/test_comp_h8_003.py`

## Verification
34 task tests passed; shared cross-task integration has 18 tests. Restore all five H8 source deltas before running task suites. These results are local technical evidence, not product acceptance.

## Run
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h8_003 -v
```
