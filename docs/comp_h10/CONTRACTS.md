# COMP H10: explicit state/motion composition and action realization

## Source and scope

Parent: `BIE-COMP-H9-005`, exact integrated archive SHA256
`295628ff2a5d076117a6e87aad66536962a32f7beb28c43673390fe2017e5d4e`.

This is an extension of the recovered DSL + COMP workspace, not a replacement
architecture or a canonical GitHub integration. Tasks derive from the existing
H3-R01/H3-R02 consolidated findings. No new original roadmap numbering is used.

Three concrete H9 observations motivate this work:

1. A native `static_focus` capability request passed with no tracks: registry
   availability was incorrectly treated as realization.
2. A state-hidden layer was still tested as visible for overlap and could block
   a valid alternate-content scene.
3. Every state `visible`/`opacity` binding on an animated target was rejected.
   This preserved safety but left ordinary combined lesson behaviors unsupported.

The H9 reproductions are retained in `H9_REPRODUCTIONS.json`. H10 preserves the
old no-consent rejection and adds an explicit contract for supported composition.

## Explicit contract

Alongside the existing `metadata.compiler_h6` runtime declaration, use:

```json
{
  "compiler_h10": {
    "schema_version": "bie.comp-state-motion-composition.v1",
    "compositions": [{
      "target_id": "e0",
      "track_ids": ["trace"],
      "state_properties": ["visible"],
      "policy": "outer-state-controls",
      "source_refs": ["fixture:h5"],
      "reasoning_refs": ["reasoning:h5"]
    }]
  }
}
```

The row must bind exactly every track on the target and every combined
visible/opacity state property. Source/reasoning references cover target and
track provenance and must be bound to the scene. Missing, duplicate, orphan,
unknown and stale declarations fail closed. There are at most 128 rows.

Semantics, from innermost to outermost:

* Base element or explicitly bound literal text content.
* Content-replacing consumers, such as equation/graph/simulation states.
* State visibility and nonconflicting state opacity controls.
* Existing geometry-only animation wrappers in their governed order.

Controls sit outside content replacement but inside geometry-only wrappers. This
avoids structural overflow from a fixed-size control box around a translated
child, without clipping content or loosening measurement thresholds.

Thus content replacement cannot swallow visibility/opacity, and binding literal
text cannot swallow its geometry animation. Hiding a subtree does not pause its
clock. Showing it later resumes the state for that absolute scene frame, not a
new playback cursor. Reverse/random access must produce the same result.

State opacity combined with any opacity-owning track is still rejected: H10
does not infer multiplication, blending or last-writer-wins for competing opacity
writers. Visibility plus a fade is supported; nonconflicting opacity plus a
camera, graph, equation or analytic-simulation consumer is supported. H6 caption
ownership restrictions remain. Arbitrary interactive writes are not added.

Original no-extension inputs keep their old conflict policy and generated
source when unaffected by one of the corrected checks.

## Layout and target following

The existing exhaustive frame-layer iterator now incorporates validated runtime
visibility/opacity, while retaining its layer rectangle and transforms. A hidden
rectangle is not reported as an occluding layer. When it becomes visible, normal
bounds/overlap checks apply from the actual quantized frame. A target-following
highlight uses that same visible-state decision. Clipping and paint remain
separate checks; a hidden layer does not skip its source validation.

## Required action realization

Native non-`render` capability requests require at least one matching emitted
track on the requested target. A registry entry alone is not enough. Missing
required behavior is `REQUIRED_ACTION_NOT_REALIZED`; missing optional behavior is
`OPTIONAL_ACTION_NOT_REALIZED` and is recorded as not realized. Invalid parameters,
wrong targets, blocked track stubs and unmatched actions cannot satisfy requests.
`render` is discharged by the element emitter. Existing unsupported/fallback
verification remains in its existing path; no fallback is invented.

The witness records exact generated source-byte SHA256, source/target identity,
track IDs and references. It is source evidence, not rendered-behavior proof.

## Diagnostic conformance

`verify_comp_composition.py` regenerates the scene under the checked compiler,
executes all frames in reverse and forward order through the inherited explicit
React/Remotion API-double bridge, and compares against the independent Python
runtime evaluator. It detects dropped/duplicated controls, missing tracks, wrong
nesting, alpha/visibility disagreement, missing frames and reverse-seek drift.
At most 2,000 frame executions are allowed; exceeding the bound never substitutes
a sampled pass. It is not an OS sandbox or a real-render authorization receipt.

Example using the retained synthetic fixture:

```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python scripts/verify_comp_composition.py \
  --scene fixtures/comp_h10/trace.json --output /tmp/bie-h10-new-run \
  --width 1280 --height 720 --fps 12

PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python scripts/validate_comp_h10.py \
  --output /tmp/bie-h10-new-matrix --browser
```

Full local regression:

```sh
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

## Evidence boundaries

The browser diagnostic uses actual Chromium but explicit API doubles, not actual
React/Remotion. It measures every frame in selected technical scenes. It does not
establish actual video/audio output, speech correctness, mathematical proof,
instructional equivalence or real-book acceptance. No dependency or sandbox gate
was disabled to report a render.

Full pinned execution remains through the existing `validate_checked_remotion.py`
and render pipeline. An environment-blocked attempt is a blocked attempt, not an
extra implemented capability and not a passing render.

## Documentation references checked in this batch

* Remotion `useCurrentFrame`: https://www.remotion.dev/docs/use-current-frame
* Remotion animation properties: https://www.remotion.dev/docs/animating-properties
* React passing children through components: https://react.dev/learn/passing-props-to-a-component

The inherited Remotion 4.0.506 / React 19.0.0 / TypeScript 5.9.3 declarations were
not upgraded. Web documentation does not substitute testing those pinned bytes.
