# COMP H5 — Specialized motion consumers

Status: implementation batch against existing finding H3-R02. This is NOT a full section re-audit. The COMP section remains open and product acceptance remains false.

## Purpose and producer/consumer boundary

This batch makes approved camera, equation-step and graph-trace decisions executable in the existing generated scene, rather than merely carrying animation metadata. The upstream Director/Animation/Math engines remain responsible for choosing appropriate teaching actions, supplying correct derivations and justifying reduced-motion alternatives. A compiler consumer must neither invent a derivation nor present its syntactic validity as mathematical truth.

Existing Scene IR action names `camera`, `morph`, and `trace` are reused. Explicit `parameters.schema_version = "bie.comp-specialized-motion.v1"` opts into the supported contract. Unversioned or unsupported specialized actions remain rejected. The existing H3 checked-source orchestration version stays intact; the new contract version and compiler/toolchain byte identity identify this extension. Existing non-specialized emitter output is not rewritten.

## H5-001 — Contracts and bindings

`specialized_motion.py` validates exact consumed fields, bounded finite values, unique nonempty provenance, declared target identity and scene sampling. State references must be subsets of the track and target references. Camera viewports bind to the element's actual pixel dimensions at the selected compilation target. Morph state zero must equal the original expression. Each equation state needs at least one pure displayed sample; undersampled schedules fail rather than silently omit a state. Existing animation property-ownership conflicts remain enforced.

Public specialized emitters also check their input/source binding; checking only at a high-level orchestrator is insufficient. Errors retain stable machine-readable prefixes. No implicit projection, units, smoothing model, easing or source coordinate normalization is introduced.

## H5-002 — 2D camera

The camera is a bounded 2D orthographic focus/zoom consumer, not a perspective/3D camera or a crop viewport. It takes explicit element-pixel viewport width/height and `from`/`to` poses (`focus_x`, `focus_y`, `zoom`). Linear and smoothstep interpolation use integer frame indices, explicit fps, and the inherited final-included-frame policy.

For a point in element coordinates: `screen = (world - focus) * zoom + viewport_center`. Generated React uses `useCurrentFrame()` and `useVideoConfig()`, not CSS time transitions. Scale and translation are applied to a children-preserving wrapper. The same pose calculation feeds exhaustive layout envelopes. Camera motion can make labels too small even while geometry is in bounds; browser content-fit evidence remains separately required.

## H5-003 — Equation steps

Only `typeset-state-crossfade` is implemented: 2–12 explicit bounded LaTeX states, per-state alternative text, source/reasoning references, and a transition fraction. The existing isolated MathText-to-SVG backend typesets the states; raw LaTeX is not passed off as rendered mathematics. Unsupported expressions fail through the existing typesetter boundary.

States have a pure hold interval and then an explicitly represented opacity crossfade. Side conditions are retained. This is NOT symbol-matched morphing, automatic algebra, proof checking, or a pedagogical-equivalence certificate. The original equation renderer is replaced only at the innermost content position so outer generic motion and camera wrappers remain effective regardless of input ordering.

An exact-key compile-local typesetting cache avoids repeated identical work. Keys bind expression, element identity and font size; cached structures are copied, not shared for mutation. No cross-compile cache bypasses toolchain or font identity checks.

## H5-004 — Signed-data polyline trace

Supported input: a graph with 1–8 identified series, 2–2,048 finite points per series, explicit increasing x/y domains, labels and units. The chosen series uses SVG path-length-normalized dashes and an optional moving head. Progress is explicitly SCREEN ARC LENGTH, not elapsed physical time, x-coordinate time or a scientific simulation.

All signed source points, other series, axis endpoints, labels and units remain present. Invalid/out-of-domain points, extra dimensions, ambiguous series identifiers and numerically collapsed neighboring vertices are rejected. There is no silent clipping or inferred normalization. Endpoint evaluation returns the exact original first/last values. The contract viewBox and emitted SVG viewBox share the same series-count-dependent height. Browser evidence compares the head against the browser's own path-length/point-at-length geometry, not only a duplicate Python formula.

## H5-005 — Existing-path adoption

`animation_track_compiler`, `scene_behavior_qa`, `qa_scene_compile` and the H3 checked publication path consume the versioned contracts. Existing source maps retain original source/reasoning associations. A content replacement cannot swallow camera/generic wrappers. The CLI adds explicit `--width`, `--height`, and `--fps` without changing inherited defaults, because a source-bound camera cannot ignore its viewport target.

Reduced-motion compilation with specialized tracks is rejected until an upstream learning-preserving specialized alternative is supplied. A generic fade must not erase an equation sequence or replace a trace with static unexplained content. State/event/audio consumers and specialized reduced-motion alternatives remain open work in the same consolidated backlog.

## Verification and evidence levels

1. Atomic Python contract and negative tests.
2. Actual installed TypeScript parsing/transpilation plus strict typechecking against clearly labelled ambient API declarations. This does not verify the complete pinned React/Remotion dependency tree.
3. Generated component and whole-scene execution through explicitly labelled React/Remotion doubles; reference comparisons, nested-wrapper retention and source maps.
4. Actual Chromium layout measurements at EVERY integer frame, plus an independent exhaustive semantic DOM/SVG pass. Network requests are aborted. Browser is launched with `--no-sandbox`; this is not an operational OS sandbox.
5. Fresh subprocess source-repeatability cases with fixed expected source failures.
6. Actual existing render-validation entry point. Missing pinned dependencies must block before composition discovery or rendering; no double replaces that stage.
7. Ordered atomic restoration, full cumulative regression, payload checksum and parent-lineage verification.

An initial exploratory browser run found two font-floor violations when zooming text/side conditions. Original cases and failed evidence are retained; separate explicitly changed camera settings are confirmatory technical variants. They are NOT an automatic repair claim or a proven teaching-equivalent alternative. No content-fit threshold is lowered to make these examples pass.

## Reproduction

From the integrated workspace, with its recorded Python/TypeScript/Chromium prerequisites available:

```sh
PYTHONPATH=app:. python -m unittest discover -s tests -v
PYTHONPATH=app:. python scripts/run_comp_h5_source_benchmark.py --output /absolute/new/source-evidence
PYTHONPATH=app:. python scripts/validate_comp_h5_consumers.py --output /absolute/new/browser-evidence
PYTHONPATH=app:. python scripts/compile_scene_checked.py fixtures/comp_h5/combined-consumers.json /absolute/new/checked-project --width 1280 --height 720 --fps 24
PYTHONPATH=app:. python scripts/validate_checked_remotion.py /absolute/new/checked-project --browser /usr/bin/chromium
```

The last command must fail closed when pinned dependencies are absent. `--install` is a separate opt-in network action, not a test success substitute. Source publication alone does not certify layout or rendering.

## Explicit remaining limits

No real pinned-project compile/render acceptance; no operating-system/network isolation; no arbitrary 3D camera, symbol matching, proof checking, general-curve/map trace, event/state/audio consumer, locale-wide readability or real-book educational assessment. Parent fixtures and source originals are preserved, not rewritten to hide these limits.
