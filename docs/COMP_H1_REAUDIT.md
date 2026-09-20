# COMP H1 re-audit — implementation evidence, not acceptance

## Decision

COMP remains IN PROGRESS. H1 addresses five parent findings under explicit bounded contracts and adds checked publication/render entry adoption. This is not section exit, complete security assurance or product acceptance. F04 and F09 are resolved in part by rejecting invalid/underspecified inputs, not by accepting the old bad inputs or claiming automatic projection/repair.

| Parent finding | H1 behavior | Evidence and remaining boundary |
|---|---|---|
| F01 JSX-like literal executed | JSON literal child encoding for text/annotation/callout | Adversarial literal roundtrips and controlled generated-TS execution; actual browser rendering still unverified |
| F02 non-bar becomes bar | Distinct native line/area/scatter/pie geometry | Actual TSX structures + numeric/strict-type tests; no frame-level equivalence claim |
| F03 sign lost | Zero-inclusive linear domain and signed baseline | Mixed/all-negative/all-zero geometry tests; extreme-dynamic-range/subpixel visual fidelity still needs review |
| F04 z dropped | Explicit orthographic matrix, full labels/components; missing or hiding projection blocked | Explicit 3D positives and missing/degenerate negatives; not a general 3D scene renderer |
| F09 invalid topology | Validated simple undirected normalized graph; invalid indices/duplicates/self-loops blocked | Isolated-vertex/valid topology and rejection tests; no directed/multigraph/autocorrection claim |
| Gate adoption | Checked source publication and real render API revalidation; full dependency typecheck before renderer | Tamper/identity/coverage tests; code-author trusted workspace, not whole-enterprise orchestration or multi-tenant sandbox |

## Remaining implementation work carried into H2

F05 requires an actual equation-typesetting adapter and layout evidence, not a raw expression text block. F06 requires supported executable simulation semantics and solver/state/provenance contracts rather than a JSON dump. F07 requires time-evaluated property application and frame-change evidence, not metadata-only progress. F08 requires declared real map projection/data/asset handling rather than a CRS label.

The original all-families task sequence is implemented locally, but these four original behavioral gaps remain reproduced in the current corpus and blocked at checked publication. Keep the original negative fixtures after fixes, add positive real behavior evidence and version expectations.

## Additional residual review items

**H1-R01 — rendering and layout validation.** Native emitted geometry has not been inspected as real rendered frames. Verify layout at supported output sizes, long labels, pie differentiation/legend, axis readability, low contrast, negative values, multilingual text, overlays, clipping, dense datasets and generated composition scaling. Fail-closed dense-label guards are not an adaptive layout solution.

**H1-R02 — numeric/visual resolution.** The implementation rejects nonfinite values, unsafe JSON integers and invalid scales, but does not guarantee visible resolution for every finite dataset spanning extreme magnitudes. Subpixel chart marks and vanishing slice ratios need a governed disclosure/aggregation/rejection policy and tests. Do not call the chart capability universally complete.

**H1-R03 — whole-scene adoption and semantic coverage.** The existing diagnostic assembler plus checked publisher is a tested source path, not the final autonomous lesson/video orchestrator. Upstream production callers must use it (or an equally enforced production implementation), bind all required scene state/assets/audio/motion and retain provenance. Unsupported required properties must not be dropped. The retained legacy fixture route is diagnostic-only and cannot bypass checked rendering.

**H1-R04 — dependency and execution trust.** No pinned dependency installation/full compile/render occurred. Version checks, hashes and static AST rules do not authenticate arbitrary dependency contents, stop adversarial time-of-check/time-of-use races, or supply OS isolation. Production security, reproducible dependency locks, library API compatibility, bounded resource behavior and real renderer evidence remain open.

**H1-R05 — educational/product acceptance.** Synthetic domain labels are not tested subject packs, actual textbook grounding, correct teaching, playable games, improved learner outcomes or continuous-learning acceptance.

## Gate policy

Do not fabricate original QA-006 or mark the COMP section complete. Next action is governed H2 scoping/implementation for F05/F06/F07/F08 with the residual review items retained. Derive exact new hardening tasks from source contracts and their dependencies before assigning identifiers. Do not rebase old goldens, weaken parser/typecheck gates or reclassify a double as real render evidence to turn a blocked run green.
