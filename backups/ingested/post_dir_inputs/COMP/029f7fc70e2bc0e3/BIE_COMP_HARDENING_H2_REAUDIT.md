# COMP H2 capability re-audit

**Decision: retain COMP in progress. No section exit or product acceptance.**

## Targeted findings and observed results

| Prior finding | H2 implementation result | Scope that remains open |
|---|---|---|
| F05 — raw typesetting | Supported Mathtext input produces real glyph geometry; safe native MathML is separately supported; original supported source fixture now passes | Full LaTeX, cross-browser/native math typography, dense equations and final lesson layouts |
| F06 — state dump called simulation | Three versioned analytic models generate time-dependent state/geometry with units; unknown original toy models are rejected instead of dumped | Arbitrary models, numerical solvers/controls, observed execution, domain/learner acceptance |
| F07 — metadata-only motion | Six generic actions change visible styles/positions; the original reveal fixture now passes | Specialized camera/morph/trace/state bindings, reduced-motion variant resolution, collision-free scene layout |
| F08 — unverified geographic projection | Two declared geographic projections emit independently checked coordinates and real SVG layers; missing projection is explicitly rejected | Antimeridian handling, tiles/assets, geodesics, advanced cartographic layout and multidomain book validation |
| H1-R03 — adoption | H2 producers, consumers, behavior sidecar and guards are used by checked publication; the real render gate remains enforced | Complete lesson/audio/game orchestration and every legacy entry path are not accepted |

These are bounded implementation closures, not a claim that every original input can now run. Original unknown-model and undeclared-projection fixtures remain intentional rejections. The historical source documents and defective emitter bytes have not been replaced to hide failures.

## Additional defects caught during H2

1. **Multiline backend error broke QA receipts.** Actual unsupported Mathtext syntax emitted control characters that the receipt token validator rejected. The receipt boundary now escapes controls without removing the failure or weakening the validator. Regression checks preserve unsupported-input blocking and strict raw-token rejection.
2. **Empty side-condition array failed strict TypeScript.** Real tsc with explicit ambient API doubles found implicit-any inference. The generated array is now explicitly `string[]`; the strict check passes. This was a genuine generated-code correction, not a softened test.
3. **Tight SVG canvas clipped equation ink.** Chromium paint/DOM bounds showed a radical/descender extending just beyond the canvas. Explicit proportional view-box padding fixes the reproduced case, and a source regression plus browser bounds check covers it.
4. **Browser fixture expectation was too strong.** A reveal could fully expose a narrow test child by its middle frame, making middle/final screenshots identical although clip values differed. The final positive fixture spans the reveal window; endpoint and visible-pixel checks remain. This was a test-fixture correction, not a claimed compiler bug.
5. **Permitted motion can leave composition bounds.** Inspection of an earlier test fixture showed a large rotated/translated child crossing the viewport. H2 does not claim an automatic spatial envelope gate. The final bounded positive fixtures are within bounds, but the general production gap remains R01 below.

The initial browser receipts/screenshots remain under `validation/comp_h2/browser_run_001` and `_002`. Only `_003` is the final browser run. Earlier failures are history, not passing acceptance evidence.

## Remaining hardening work, grounded in this workspace

### H2-R01 — Whole-scene visual/layout constraints (implementation gap)

The source gate validates declared boxes and behavior contracts, but does not prove every frame's transformed ink stays within its allowed region. Long layer labels can also compete for a fixed legend cell, and a geometrically correct equation can be unreadable in a tiny box. Next hardening should define scene-space motion envelopes, permitted intentional overshoot/crop, box-aware text/legend/equation fit, and inter-element occlusion rules. Add extreme/range fixtures and inspect actual frames. Do not convert syntactically valid geometry into a blanket VIS/learning pass.

### H2-R02 — Whole-scene consumers and accessibility (implementation gap)

The checked assembler continues to block events, narration/interaction/state bindings and simulation controls that it does not consume. Specialized animation families and declared reduced-motion variant references are not fully resolved into production outputs. Extend real producer-to-consumer integration with explicit capability negotiation; do not merely remove the blockers or declare all existing modules integrated. Preserve source/reasoning/asset provenance across each adopted path.

### H2-R03 — Execution/toolchain identity and safety (implementation + operational gap)

Generated math geometry records font hashes/backend versions, but generic pre-generation dependency-context keys do not fully bind every host Python/native font/backend condition. Cross-environment repeatability and cache eligibility need explicit host-toolchain identity. Mathtext uses guarded global matplotlib settings, but unrelated concurrent matplotlib clients are outside that local lock; process isolation is preferable for a production worker. The source receipt is not an attestation of the whole node_modules tree or a hostile-code execution sandbox. Dependency/asset integrity, concurrency, resource budgets and OS isolation remain governed work.

### H2-R04 — Real dependency compile and Remotion output (environmental/acceptance blocker)

The actual local TypeScript parser/compiler is 5.8.3; the unchanged generated project requests 5.9.3, React 19.0.0 and Remotion 4.0.506. Registry access failed with EAI_AGAIN. The checked real harness stops at FULL_TYPECHECK_BLOCKED/BLOCKED_DEPENDENCIES. No full generated-project compile, actual Remotion composition discovery, smoke render or full render was verified. Eleven browser-painted component cases are useful narrower evidence, not a substitute. Recover registry access/approved caches, run the full exact project, inspect rendered frames and audio, and preserve independent media/artifact receipts.

### H2-R05 — Book, subject and learning acceptance (product-level gap)

Fifty-nine synthetic source fixtures across ten domain labels do not establish correctness on ten complete subjects. The analytic model registry has three adapters, not a general scientific simulation engine. Real books, prerequisites/math/reasoning fidelity, expert review, learner comprehension, narrated lesson quality, playable-game integration and reproducibility are still required. No percentage-complete or acceptance score is inferred from test counts.

## Next phase

Continue **COMP hardening H3 scoping and implementation**, using R01–R03 and the existing H1 numeric/visual-resolution findings to select the next atomic contracts. Keep R04 and R05 visible rather than labelling them complete. Derive IDs in a new governed registry before coding; there are no invented next original COMP tasks and no mandatory exit after a re-audit.

No GitHub modifications or commits were performed in H2. Canonical repository adoption remains a distinct later verified action under the established section workflow.
