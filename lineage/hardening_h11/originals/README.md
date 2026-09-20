# BIE cumulative DSL + COMP — H11

Checkpoint `BIE-COMP-H11-004`: verified image/video handoff, explicit image crop, video trim/lifetime and existing-path adoption. This extends the exact supplied H10 workspace, not the complete canonical BIE monorepo. COMP remains IN PROGRESS and product NOT ACCEPTED.

Read `docs/comp_h11/CONTRACTS.md`, `docs/comp_h11/SCOPE.json`, the consolidated gap ledger and `CONTINUATION.json`. Full release evidence is in the separate H11 Master Backup and final verification report bound to this integrated ZIP's SHA256.

## Execute from the extracted workspace

```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests/compiler -p 'test_comp_h11_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_comp_h11.py --output /tmp/bie-h11-new-run --browser
python scripts/compile_scene_checked.py fixtures/comp_h11/trim-video.json /tmp/bie-h11-new-project --asset-root fixtures/comp_h11/asset_root --width 640 --height 360 --fps 12
python scripts/validate_checked_remotion.py /tmp/bie-h11-new-project --timeout 120
```

Output directories must not exist. Existing pinned Python dependencies, Node, TypeScript, Chromium, FFmpeg/ffprobe and the existing H7 Linux worker prerequisites are required. The last command does not install dependencies unless `--install` is explicitly requested; the full pinned project and production isolation must be available before actual rendering.

For a previously bundled source, use `python scripts/bind_visual_assets.py scene.json bundle_receipt.json asset-root /tmp/bie-new-binding`, then publish its `BOUND_SCENE.json` with the same asset-root. Do not handwrite a claim that media bytes are verified.

The native-browser diagnostic uses explicit React/Remotion API doubles and muted technical videos. It is not a Remotion render, audio-playback proof, actual-render authorization or educational acceptance.

## Restore and integrate

Use the separate Integrated ZIP directly. Atomic ZIPs are ordered deltas against exact H10; restore all FOUR before testing because cross-task dependencies are deliberate. Intermediate stages are source assembly, not standalone executable releases. The Master contains the same integrated ZIP, current task ZIPs/evidence/checksums, not recursively embedded older Masters. No GitHub files changed; canonical integration still requires repository-side path/provenance/regression verification and a real commit SHA. Changed H10 originals are preserved under `lineage/hardening_h10/originals`.
