# BIE-COMP-H8-005 — Actual-producer adoption and witness integration

Inherited finding: H3-R01/H3-R02. Parent checkpoint: BIE-COMP-H7-008.

## Implemented contract
Wire original-Scene renderStill inputProps to all counterfactual modes, frame/nonce inventory, restore checks and PNG hashing; add raster analysis to the existing process-owned witness conjunction with fit and paint QA. The original Scene is not swapped for a diagnostic renderer. Kernel/pinned-dependency gates remain. Real installed tsc exercises instrumented helper typing with labelled declarations; controller protocol uses explicitly fake packages in tests. Neither establishes actual pinned Remotion execution.

## Files
- `app/bie/compiler/real_paint.py`
- `app/bie/compiler/qa_support/remotion_raster_capture.cjs`
- `tests/compiler/test_comp_h8_005.py`
- `tests/compiler/test_comp_h8_controller.py`
- `tests/compiler/test_comp_h8_integration.py`

## Verification
23 task tests passed; shared cross-task integration has 18 tests. Restore all five H8 source deltas before running task suites. These results are local technical evidence, not product acceptance.

## Run
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h8_005 -v
```
Also run `tests.compiler.test_comp_h8_controller` (8 of the 23 task tests) and `tests.compiler.test_comp_h8_integration`.
