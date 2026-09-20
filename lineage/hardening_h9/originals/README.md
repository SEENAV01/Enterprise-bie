# BIE cumulative DSL + COMP — H8

Checkpoint: BIE-COMP-H8-005. This is an extension of the exact supplied H7 workspace, not the whole canonical BIE repository. Section remains IN PROGRESS; product NOT ACCEPTED.

See `docs/comp_h8/RESULT.md`, `docs/COMP_CONSOLIDATED_GAP_LEDGER.json` and `CONTINUATION.json`.

## Execute
```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=app python scripts/inspect_comp_coverage.py
PYTHONPATH=app python scripts/verify_comp_raster.py --scene tests/fixtures/comp_h8/map.json --out /tmp/bie-new-pixel-run --fps 4
```
The coverage CLI deliberately returns 2 while declared consumers are missing. The raster CLI is DIAGNOSTIC (actual Chromium, explicit React/Remotion API doubles), not a real Remotion render. Output directory must not exist. `requirements-comp-raster.txt` records supplemental tested Python dependencies; it does not replace earlier compiler/math/toolchain dependencies. Chromium, Node and tsc must be installed. No automatic dependency installation or permissive renderer fallback is added.

Actual rendering continues through the existing checked compile/render path, requiring pinned dependencies, kernel profile, byte identities and a process-owned actual-render witness. Real runtime execution remains blocked here.

## Restore and integrate
Use the separate cumulative Integrated ZIP directly. Atomic ZIPs are ordered deltas against exact H7; restore all five before testing. Master embeds the identical Integrated ZIP, deltas and current evidence, not recursive previous Masters. This delivery has not been committed to GitHub. Preserve repository provenance and run canonical integration tests before claiming that status. Original README and changed files are in `lineage/hardening_h7/originals`.
