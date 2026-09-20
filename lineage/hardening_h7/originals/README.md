# BIE COMP — H7 cumulative integrated workspace

Checkpoint **BIE-COMP-H7-008**. This is DSL + COMP, not the complete canonical BIE monorepo. H7 delivers eight consolidated hardening task contracts. **Section exit and product acceptance are false**: broader inherited visual/specialized coverage remains open, and real pinned rendering/private-proc browser execution is blocked.

Start with `docs/COMP_H7_REAUDIT.md`, `docs/COMP_H7_SCOPE.json`, `docs/COMP_H7_SPEC.md`, `BATCH_MANIFEST.json` and `CONTINUATION.json`.

## Local tests
```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
PYTHONPATH=app:. python -m unittest discover -s tests -p 'test_comp_h7*.py' -v
```
Dependencies and platform details are in the specification. The source ZIP does not bundle Node packages, binaries or font files. Diagnostic TypeScript 5.8.3 plus API declarations is not a substitute for generated TypeScript 5.9.3 / React 19.0.0 / Remotion 4.0.506.

## Supplied dynamic narration + repair technical example
Choose new output directories; existing outputs are never silently overwritten.
```bash
PYTHONPATH=app:. python scripts/compile_scene_checked.py \
 examples/comp_h7/dynamic_narration_scene.json /tmp/bie-h7-repaired \
 --asset-root examples/comp_h7/assets \
 --layout-policy examples/comp_h7/repair_policy.json \
 --layout-evidence /tmp/bie-h7-repair-evidence \
 --width 1280 --height 720 --fps 24 --browser /usr/bin/chromium
PYTHONPATH=app:. python scripts/validate_comp_h7.py --output /tmp/bie-h7-technical-validation
PYTHONPATH=app:. python scripts/benchmark_comp_h7.py --output /tmp/bie-h7-source-benchmark
```
The validation script intentionally attempts and records environment-blocked real rendering after diagnostic checks. Its Chromium scenes use clearly labelled React/Remotion doubles; technical audio is synthetic tone. No narrated lesson, real video or game acceptance follows.

## Actual render path
Use `scripts/run_comp_render.py request.json --mode full` with the checked source workspace, exact source/composition identity and an explicit browser. The real path requires installed pinned packages, production toolchain identity, isolated typecheck, private browser namespace worker and a process-owned actual-paint witness. `--mode smoke` uses the existing smoke range contract. Do not use legacy diagnostic scripts or fabricated receipts to bypass these gates. The current environment blocks before any actual render.

## Packaging and provenance
Integrated ZIP is cumulative. Atomic H7 ZIPs are ordered source deltas, all eight required before tests. The Master includes the same integrated bytes plus current deltas/evidence; previous Masters are NOT recursively embedded. Existing ancestor fixture files are retained because inherited regression requires them. New bulk browser artifacts are in the separate H7 evidence ZIP, not appended to the current source.

Changed H6 originals: `lineage/hardening_h6/originals/`. Earlier compatibility lineage references are preserved with exact ancestor bytes; no historical tests/goldens are rewritten. External final verification binds test and package results to release hashes. No GitHub write, commit or canonical merge occurred.
