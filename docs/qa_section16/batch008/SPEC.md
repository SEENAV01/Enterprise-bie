# Section 16 / Batch 008 — visual QA contract

## Scope and trust
Additive module `bie/qa/visual_v2`, original registry VIS-001 through VIS-005.
The operator supplies a separate policy defining lesson, audience, language,
scene/object/relation inventory, required responsive states and explicit limits.
The candidate cannot reduce that inventory, relabel text as decoration, remove a
critical view, invent a blanket overlap waiver or replace a source citation with
an unrelated image. Sources and output text use existing BI/KI source contracts.
Section15 is externally managed; no remote write or integration is authorized here.

## Inputs and outputs
`VisualRequest` contains a source request, visual scenes/elements, finite measured
states, source-linked relations and optional capture references. `VisualPolicy`
contains the operator-owned corresponding requirements. Geometry is integer
milli-CSS-pixels, with closed roles/vocabularies and bounded collections. Input
JSON is closed-world: unknown/missing fields, non-finite values, bool-as-int,
duplicate keys and malformed tuples are rejected. Structural JSON schemas do not
replace the stricter runtime cross-reference, byte and trust validation.

`evaluate(request, artifact_root, policy, as_of=..., ...)` returns source reports,
five task-specific reports, exact evidence/request/policy digests, native layout
fingerprints and verified capture IDs. Outcomes are `BLOCKED`, `REVIEW_REQUIRED`
or `CHECKS_PASSED` **within the stated bounded check scope**. Product acceptance
is always false. Report recomputation rejects edited or stale reports.

## Algorithms
VIS-001 validates required representation purpose, features and inventory, then
requires a current reviewed teaching judgment. It does not invent a universal
representation-quality score or claim a decorative slide is a cinematic lesson.
VIS-002 checks every required finite viewport/state, visible required content,
safe/caption areas, ancestor clipping and positive-area overlaps. Parent/group
membership never creates a waiver. Specific operator pair waivers require an
authenticated review and an exact overlap-fraction cap; distinct text-text
waivers are forbidden. Actual continuous/3D occlusion needs later evidence.
VIS-003 computes **peaks**, not averages: simultaneous foreground/semantic items,
text length/rate, exact clipped rectangle-union occupancy and local grid density.
Overlapping/repeated boxes cannot inflate union area. These are policy guardrails,
not measured cognitive load or perceptual clutter scores.
VIS-004 verifies inspected display text, font size/readiness, line extents, exposure,
combined text demand and unrounded sRGB contrast against known opaque uniform
backgrounds. Foreground alpha is composited before luminance. Unknown gradients,
filters, images or unresolved paint do not receive an average-color pass. This is
not a WCAG conformance certificate, glyph-recognition engine or reading-speed study.
VIS-005 checks source mapping, relation endpoints, explicit above/left/contains/
label-distance constraints, color-independent encodings and reviewed semantic
alignment. Causal arrows and simulations still need domain/context assessment.

## Reviews and immutable evidence
Existing purpose-scoped review authentication is reused. Request/policy/evidence,
evaluator/version, time, key revocation and operational assurance are checked.
Policy can require 1–8 independent reviewer groups; duplicated evaluators/secrets
cannot manufacture quorum. A reviewed rejection or uncertainty is not outvoted.
Positive tests use explicitly SYNTHETIC operator-managed fixtures, not operational
assessors. No signing key is configured by default or emitted with release evidence.
SnapshotStore checks actual bytes with bounded reads, hashes, lengths and confined
paths. Cross-reference aliases and aggregate capture-byte budgets are rejected.

## Static HTML observation
`capture_static_html` is opt-in for **trusted, reviewed, static HTML**. It disables
page JavaScript, service workers and network requests, and evaluates fixed collector
instrumentation. It records actual Chromium DOM/Range rectangles, computed text/
styles, fonts-ready state, clipping, a PNG and a bound measurement document.
Raw measurement documents are candidate **support** artifacts, not final QA reports;
this preserves the existing release candidate's prohibition on report artifacts.
The collector bounds DOM depth/count, text nodes, line boxes, viewport pixels,
HTML bytes and timeout. It reports untracked paint/text, active/complex content,
transforms, gradients, masks, mixed styles, group opacity, pseudo content and sampled
hit-test ambiguity as unsupported. It is **not** a hostile-code/OS security sandbox.

`verify_capture` rereads HTML/measurement/PNG bytes, validates hashes, exact state,
viewport and renderer binding, and decodes a single PNG at the expected dimensions.
That verifies identity and decodability, not universal truth of imported metadata
or arbitrary image semantics. Production collection provenance remains open.
A sample is always marked `sampled`, so it never proves all intermediate frames.
No font binary is bundled.

## Compatibility and release
Pinned canonical layout/collision modules are executed through an additive adapter.
Their byte/Git-blob identities are verified; their acceptance flags are not promoted.
The inspected commit is a historical dependency snapshot, not a claim about latest
HEAD. Current canonical code must be reread and conflict-checked before adoption.
The release bridge binds all inspected support/source artifacts to the candidate,
emits report bytes without writing or signing them, and produces `FAIL` when blocked
or `NOT_RUN` otherwise. Static samples/healthy plan checks never emit full-media PASS.
The actual inherited release evaluator rejects the incomplete unsigned bundle.

## Verification and acceptance boundary
See executed_run_008 for actual unique test IDs, dependencies, source/test hashes
and all preserved regressions; mutations_008 for targeted controls/patches; and
browser_run_008 for real static Chromium observations. Browser diagnostics and
property subcases are not additional unique unit tests. Development corrections
and an interrupted nested command are retained in development_008.
No full-repository regression, real textbook E2E, native BIE video render, gameplay,
live semantic assessor, learner study or enterprise release was executed.
Remaining scope is explicit in the cumulative gap ledger. After all original tasks,
perform full enterprise audit, justified traceable hardening and re-audit before exit.
