# COMP H6 — continuation of H5, not a replacement product

The integrated archive is the cumulative DSL + COMP workspace. It is not the entire canonical BIE monorepo, a GitHub commit, or an accepted final product. The master contains this same archive plus task deltas and current evidence. Older master archives are NOT recursively embedded.

## Run from the restored integrated workspace

Python dependencies used by inherited tests and generation include NumPy/Matplotlib. Node and TypeScript are required by source checks. Chromium/Playwright and FFmpeg/ffprobe are needed for the existing browser/media technical validations. Missing required dependencies must be treated as blocked verification, not silently skipped success. The host's global TypeScript version used locally is 5.8.3; it does not replace the pinned generated-project TypeScript 5.9.3.

```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=app:. python scripts/compile_scene_checked.py examples/comp_h6/scene.json /tmp/bie-h6-project --width 1280 --height 720 --asset-root examples/comp_h6/assets
PYTHONPATH=app:. python scripts/validate_checked_remotion.py /tmp/bie-h6-project --browser /usr/bin/chromium
```

See `python scripts/compile_scene_checked.py --help` for the exact CLI flags available. The project/output directory must be new. Installing external dependencies is an explicit operator action: the real execution harness does not silently install or downgrade packages. `--install` requests the pinned project install. This batch's real run stops at missing dependencies before rendering.

The example WAV is a generated 440 Hz technical tone, not spoken narration. Captions, hash bindings and timing can be validated independently, but no claim is made that the tone speaks the caption words. Declared rights references are preserved, not legal-rights acceptance.

```sh
PYTHONPATH=app:. python scripts/validate_comp_h6_runtime.py --output /tmp/bie-h6-dom
PYTHONPATH=app:. python scripts/benchmark_comp_h6.py --output /tmp/bie-h6-source-benchmark
```

The DOM command paints actual Chromium while substituting explicitly labelled React/Remotion APIs; it does not play audio. Its Audio markers and frame scheduling are diagnostic. The benchmark generates source in independent processes, not rendered videos. A late-text-overflow fixture is a deliberate fit rejection even though source generation passes.

## Restore atomic deltas

Use the integrated archive for a ready cumulative workspace. Atomic ZIPs are traceable ordered source deltas and are not standalone applications. Extract H6-001 through H6-005 separately; run each `APPLY_DELTA.py --base <previous-workspace> --output <new-workspace>` in order. All five must be restored before running any task suite, because those suites exercise integrated contracts. The helper never modifies its base and checks exact previous/new tree and payload hashes. Hashes prove local byte agreement, not signed external authenticity.

## Scope retained open

State.set literal changes to text/visibility/opacity, single-voice PCM16 narration and matching captions are supported. Arbitrary runtime code, writable game events, general state expressions, concurrent narration/mixing, compressed media, TTS, speech alignment and universal reduced-motion learning equivalence are not claimed. Audio asset roots combined with the static H4 automatic-repair branch are explicitly blocked pending joint dynamic repair integration. A detected overflow is not a repaired teaching scene.

Current consolidated findings remain open; no new full-section re-audit was performed. No GitHub writes. Real pinned compile/render, trusted frame QA, operational OS/network isolation and real-book/game/learning acceptance remain separate gates.
