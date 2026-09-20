# COMP Batch 009 capability audit

Date: 2026-09-18. Checkpoint: BIE-COMP-QA-005.
**Decision: COMP REMAINS IN PROGRESS. SECTION EXIT NOT PERMITTED. PRODUCT NOT ACCEPTED.**

## Scope and evidence

Read and executed the uploaded Batch 008 workspace; preserved its 388 original members before replacing only current root metadata. All 288 inherited Python files remain byte-identical. Added original QA-001..005 implementation and tests. The audit covers source-generation/QA behavior in this restored compiler workspace, not the latest GitHub tree, upstream book ingestion or all 18 BIE sections.

The complete final benchmark exercised the real inherited emitters, real local TypeScript AST parsing, source contracts and independent fresh-process generation. It matched 19 source expectations over ten domains, including nine deliberately negative fixtures that expose genuine inherited implementation defects. No full dependency-verified generated-project compile or real video rendering is established.

**921 passing tests mean the implemented contracts and expected defect detection passed. They do not mean the nine compiler defects are fixed.** Most original COMP family code has not been modified in this batch. The new fail-closed QA adapter is not automatically applied at every legacy production entry point.

## Reproduced implementation defects — OPEN

These are audit finding identifiers, not invented original roadmap task identifiers. Each points to `validation/comp_qa_009/benchmark_final/<case>/` and its source contract, fixture, generated project and case result.

### COMP-AUDIT-009-F01 — Text literal crosses the JSX execution boundary

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-jsx-braces`. Detected codes: `TEXT_LITERAL_JSX_INJECTION; QA_UNSEEDED_RANDOM`.

Closure needed: Emit text through a correctly escaped JSX string expression or safe text-node representation; test braces, angle brackets, quotes, multilingual text and hostile-looking source text. Require real compile/render text fidelity before closure.

### COMP-AUDIT-009-F02 — Requested chart kind silently becomes bars

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-chart-kind`. Detected codes: `CHART_KIND_DOWNGRADE`.

Closure needed: Implement semantic chart-kind dispatch or a blocked unsupported result. A required line/pie/scatter representation may not be relabelled as bars.

### COMP-AUDIT-009-F03 — Negative chart values lose their sign

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-chart-sign`. Detected codes: `CHART_SIGN_LOSS`.

Closure needed: Implement signed coordinate/domain/baseline handling with positive, negative, mixed, zero and degenerate data tests and image-based checks.

### COMP-AUDIT-009-F04 — A 3D vector loses its z component

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-vector-z`. Detected codes: `VECTOR_Z_COMPONENT_DROPPED`.

Closure needed: Implement a declared 3D projection/render adapter or a witnessed, approved educationally valid projection. Preserve dimensionality and units; do not silently flatten.

### COMP-AUDIT-009-F05 — Typeset equation requests remain raw text

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-untypeset-equation`. Detected codes: `EQUATION_TYPESETTING_NOT_IMPLEMENTED`.

Closure needed: Integrate a governed equation typesetting adapter with dependencies/assets/rights and overflow/error handling. Keep explicitly requested plain text separate.

### COMP-AUDIT-009-F06 — Simulation emits state labels rather than simulation behavior

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-state-only-simulation`. Detected codes: `SIMULATION_STATE_ONLY`.

Closure needed: Connect a real deterministic simulation adapter and frame-time evolution, with units, state/provenance and bounded computation. Static state display is not simulation.

### COMP-AUDIT-009-F07 — Animation progress is metadata without visible motion

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-metadata-animation`. Detected codes: `ANIMATION_TRACK_NO_VISUAL_EFFECT`.

Closure needed: Map governed property tracks to visible component/style transforms with interpolation and frame-specific tests. Verify start, intermediate and end frames; retain existing valid special handlers.

### COMP-AUDIT-009-F08 — Geographic coordinates lack proven projection

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-geographic-crs`. Detected codes: `MAP_PROJECTION_UNVERIFIED`.

Closure needed: Require and implement coordinate-reference-system/projection conversion, extents and geometry mapping. Normalized synthetic routes are not proof of geographical correctness.

### COMP-AUDIT-009-F09 — 2D model edges can reference nonexistent vertices

Status: OPEN IMPLEMENTATION DEFECT; source-QA guard implemented. Fixture: `reject-model-edge`. Detected codes: `MODEL2D_EDGE_INDEX_INVALID`.

Closure needed: Validate vertex/edge identities and topology before generation; add proper adapter or reject unsupported model geometry. Reject out-of-range, duplicate or malformed connectivity as appropriate.

## Additional adoption and coverage work — OPEN

The QA adapter requires explicit fixture layout and presently consumes a restricted set of Scene IR contracts. It blocks unsupported binding or unconsumed controls rather than inventing missing behavior. Shape/diagram/highlight adapters and full audio, state, event and interaction consumption require architecture-driven integration review. This is not a claim that every related standalone module is absent: earlier audio/animation modules exist. The missing evidence is correct producer-to-consumer adoption and coverage in the actual compilation/release path.

Fallback witnessing is stronger than the inherited plan-only resolver, but a hash-bound witness alone cannot prove equivalent teaching. Production release/build paths must enforce required semantic/source/accessibility contracts, and actual rendered evidence must establish visual correctness. Static AST policy is not a comprehensive security sandbox, and immutable goldens record source identity, not educational correctness.

The ten positive cases do not cover all subjects, layouts, expressions, charts, assets, disabilities, scripts, rendering backends or input edge cases. Technical fixtures with subject labels are not complete domain adapters or subject-pack acceptance. Expand the governed corpus based on real capability and error evidence rather than an arbitrary test-count goal.

## Environment and product validation — BLOCKED / NOT RUN

The registry probe returned EAI_AGAIN and Remotion dependencies are unavailable. Global TypeScript 5.8.3 differs from the unchanged generated project's 5.9.3 target. The strict pinned generated-project compile gate is correctly BLOCKED_DEPENDENCIES, not passed. Real Remotion CLI composition discovery, smoke render, full render and rendered-frame checks remain NOT RUN.

Book/PDF-to-IR provenance quality, upstream learning objectives, full narration/audio timing, independent subject/educational review, playable revision games, cumulative enterprise regression, release rights/security/performance and real-book product acceptance are outside this local QA verification. No canonical repository write or commit was made.

## Governed next work

Start COMP section capability audit and justified hardening, not the next section. Use these reproduction fixtures and original architecture to approve exact hardening tasks before assigning task identifiers. Preserve the parent emitters/receipts as lineage, implement needed fixes or valid adapters, add positive and negative tests, run pinned project builds and actual renders when dependencies are available, and retain explicit environment blocks until truly executed.

Prioritize the literal-text execution boundary and semantic information loss, then coordinate typesetting, animation/simulation and map/model adapters with their existing upstream/downstream contracts. These are proposed work areas, not a claim that nine ZIPs mechanically complete COMP. Re-audit after hardening; add more tasks when evidence justifies them, and do not require section exit merely because the initial audit list is resolved.

All new baseline changes after fixes must be reviewed and versioned. Do not simply regenerate goldens to turn an unintended source change green. Do not delete negative evidence or reclassify a failing semantic capability as optional merely to pass.

## What is closed in this delivery

The five original QA tasks now have executable local implementations, 154 atomic tests and 16 cross-task tests, plus a preserved 751-test baseline. A complete source benchmark and fresh-process evidence are present, with clear blocked/full-execution distinctions. These are implementation/test deliverables, not closure of the emitter defects, canonical integration or product acceptance.
