# BIE cumulative DSL + COMP — H10

Checkpoint: `BIE-COMP-H10-004`. Extension of the exact supplied H9 integrated workspace, not the whole canonical BIE monorepo. COMP remains IN PROGRESS; product NOT ACCEPTED.

See `docs/comp_h10/RESULT.md`, `docs/comp_h10/CONTRACTS.md`, `docs/COMP_CONSOLIDATED_GAP_LEDGER.json` and `CONTINUATION.json`.

## Execute
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python scripts/verify_comp_composition.py --scene fixtures/comp_h10/trace.json --output /tmp/bie-h10-new-run --width 1280 --height 720 --fps 12
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python scripts/validate_comp_h10.py --output /tmp/bie-h10-new-matrix --browser
```
Output directories must not exist. Existing Python compiler/math/raster dependencies, Node, installed TypeScript and Chromium are required. No automatic pin upgrades or silent installation is added. The composition and browser tools explicitly use React/Remotion API doubles: they cannot authorize actual rendering or claim complete educational/video acceptance.

Actual rendering continues through `scripts/validate_checked_remotion.py` and the established checked compile/render path, including pinned dependencies, kernel profile, byte identities and process-owned actual-render evidence. Required runtime dependencies remain unavailable here.

## Restore and integrate
Use the separate cumulative Integrated ZIP directly. Atomic ZIPs are ordered deltas against exact H9; restore all FOUR before testing. Master embeds the exact same integrated ZIP, current atomic deltas/evidence/reports and checksums, not earlier Masters recursively. No GitHub changes were made. Preserve repository provenance and run canonical integration tests before claiming repository integration. Changed originals are in `lineage/hardening_h9/originals`.
