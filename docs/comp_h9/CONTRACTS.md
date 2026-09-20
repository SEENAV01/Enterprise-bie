# H9 integration contracts and reproductions

This extends the frozen H8 workspace. It does not replace its compiler or original scene builders.

## Shapes / diagrams / highlights
Examples for every original shape kind and highlight mode, an explicit diagram and all actions are in `tests/compiler/h9_test_support.py`. Fully materialized technical inputs, including invalid cases, are in `fixtures/comp_h9/corpus.json`. The original shape and highlight constructors remain byte-identical. The original diagram constructor receives a backwards-compatible keyword-only `view_box` argument, so its produced object can reach the emitter directly; omitted-view-box legacy calls retain their existing props. Its predecessor bytes are preserved.

Shapes require `shape_kind`, `geometry.view_box=[x,y,width,height]` plus kind-specific coordinates, with optional bounded style. Diagrams retain `diagram_kind`, `nodes`, `edges`; their production emitter additionally requires source layout and direction instead of making up positions/relations. Highlights require exact scene context and source-bound target IDs.

## Registered actions
Every new contract declares `schema_version: "bie.comp-registered-action.v1"`. See `registered_actions.py` for strict field sets and the fixture corpus for complete runnable input examples. Registry names alone never mean arbitrary parameters are supported.

| Action | Executed behavior | Important bound |
|---|---|---|
| `simulation_state` | Actual analytic model clock maps to an explicit start/end track window. | Same model and source endpoints; frame sampling validated. |
| `static_focus` | One fixed 2D orthographic focus/zoom pose. | Explicit element-pixel viewport must match target geometry. |
| `static_trace` | Complete source polyline including signed axes/units. | Existing graph contract and series identity. |
| `crossfade_states` | Actual typeset source equation states crossfade. | Preserves side conditions/references; no symbolic proof. |
| `state_snapshots` | Static analytic-model observations at bound timeline milestones. | Initial/final model states retained; references are not expert verification. |
| `progressive_static_trace` | Whole source polyline progressively appears in static milestones. | All source vertices and endpoints included, no unsampled milestone. |
| `path_endpoints_with_progress_marker` | Original static source path + endpoint labels + stationary numeric progress. | Explicit source line/polyline geometry and viewport; no moving source object. |

## Local evidence commands
```bash
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=app:. python scripts/inspect_comp_coverage.py
PYTHONPATH=app:. python scripts/validate_comp_h9.py --output /absolute/new/h9-browser-evidence
PYTHONPATH=app:. python scripts/run_comp_h9_source_benchmark.py --output /absolute/new/h9-source-evidence --runs 2
```
Browser tests require an actual locally installed Chromium and TypeScript, but use explicitly labelled React/Remotion API doubles. They are diagnostics, not actual Remotion rendering or a browser OS sandbox. The full-render entry and process-owned checks remain required; `--install` on the existing validation harness is explicit opt-in.

## Historical test migration
H8's live-coverage tests expected three element and seven action names to stay unavailable. Their active expectations now assert the actual implemented names and still reject removed dispatch and invalid parameters. The old QA integration negative example used a `shape` with invalid `kind` props; it still rejects, now with `PRIMITIVE_FIELDS_INVALID`, not the obsolete missing-emitter code. Exact originals are retained under `lineage/hardening_h8/originals/tests/compiler/`. No historical golden fixture is edited. Earlier lineage tests are satisfied by restoring exact ancestor bytes, not by weakening preservation assertions.

## Remaining boundaries
Name coverage is complete for the current live registry. Full installed dependency compilation, actual Remotion video/counterfactual capture, whole-image/locale/cartographic review, real-book pedagogical quality and reduced-motion teaching equivalence are not certified. Do not infer section exit from 34 dispatch entries or local passing tests.

### Context-only compatibility baselines
`fixtures/comp_h9/legacy_qa_compat/` is an explicit context migration, not a regenerated golden blessing changed output. It refused any changed generated file hash or byte count in the 19 original H2 corpus cases; their corpus bytes and original goldens stay immutable. Only the capability adapter-context identity and bound snapshot hash change. The old context is still rejected by a negative test. The original builder extension is separately tested for legacy-props parity and direct production-emitter consumption.
