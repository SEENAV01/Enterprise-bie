# COMP Hardening H2 — specification and production boundaries

Delivery sequence 11; parent H1-005; compiler identity `1.2.0-comp-h2`.

This extends the original COMP workspace. The five audit-derived IDs were scoped in `governance/COMP_H2_TASK_REGISTRY.json` before implementation. The prior source, tests, original fixture documents, baselines and archive lineage remain recoverable. This is **not** a redesign, an accepted section exit, a complete subject pack, or autonomous real-book execution.

## H2-001 — Equation typesetting

Files: `equation_typesetting.py`, `equation_compiler.py`.

The `latex` contract now invokes the real pinned Python Matplotlib 3.10.8 Mathtext backend at compile time. It produces native SVG glyph paths and fractions/radicals/superscripts rather than displaying raw LaTeX. The backend uses the DejaVu math font set, explicit path output and stable SVG IDs. Generated geometry records the input hash, adapter/backend/FreeType versions and hashes of the fonts actually used. Font files are not copied or redistributed. The generated React component recursively constructs a small inert SVG vocabulary, not `dangerouslySetInnerHTML`. Local glyph references must resolve to defined IDs; external resources, CSS injection and unknown markup fail closed.

This is the **Mathtext subset**, not arbitrary TeX/LaTeX. Unknown commands, external resources/macros, malformed grouping, dollar delimiters and multiline math are rejected. Input is bounded to 2,048 characters, nesting 24 levels, 512 glyphs and 1.5 MB output; extreme aspect ratios are rejected. Backend unavailability or a version mismatch is an error, never raw-text fallback. Native MathML is a separate allowlisted tree contract, bounded to 12,000 input characters / 512 nodes / 24 levels. It requires a math root, token text, supported namespaces, explicit structural arity and safe attributes; executable/remote markup is blocked. Plain text is still an explicit separate format.

A real browser paint test exposed tight backend view boxes clipping a radical/descender. The output now expands the view box by `max(1 SVG unit, 4% of original height)` on every side, and a regression test preserves this rule. Browser checks confirm this representative fraction/radical stays inside its frame. This does not establish legibility for every equation or every lesson layout. Native MathML depends on the browser's math-font support, unlike path-based Mathtext.

## H2-002 — Executable analytic simulations

Files: `simulation_models.py`, `simulation_compiler.py`.

Three explicitly versioned, closed-form model adapters are implemented:

| Model | State/parameters | Evaluation |
|---|---|---|
| `bie.sim.constant-acceleration-2d@1` | x, y, vx, vy; ax, ay; SI units | x=x0+vx0*t+ax*t²/2, y=y0+vy0*t+ay*t²/2; velocities update |
| `bie.sim.harmonic-oscillator-1d@1` | x, v; positive omega; m, m/s, rad/s | Undamped x=x0*cos(omega*t)+(v0/omega)*sin(omega*t), with analytic velocity |
| `bie.sim.exponential-decay@1` | nonnegative n; nonnegative rate; dimensionless n and 1/s | n=n0*exp(-rate*t) |

A simulation specifies its model identity, `execution_class: analytic_model`, exact state/parameter keys, units, start/duration and view bounds. Coerced strings/booleans, nonfinite values, unknown fields, invalid units and out-of-contract magnitudes are rejected. Time is derived from the composition frame and fps and clamped at the model endpoints. A deterministic sampled path, current state marker and numeric state with units are emitted. The dashed path is explicitly the **full model trajectory**, not a measured trace.

These adapters are not general physics solvers. Observed-execution claims and an arbitrary receipt reference do not establish measurements and are rejected. The compiler exposes assumptions and separates analytic model output from observed evidence. Model source and numeric helpers are cross-checked against independent analytic/differential/RK4 expectations; emitted JS is executed through an explicit test hook runtime. Browser evidence shows the marker moving at sampled frames.

Duration is bounded to 600,000 ms; initial/parameter magnitudes to 1e8, evaluated values to 1e12, and trajectory size to 65..4097 samples. The declared view must contain analytic extrema; clipping is rejected rather than hidden. Oscillator sampling must be sufficient both for trajectory discretization and rendered frames. The final model time must actually appear on a sampled scene frame: a nominal two-second simulation inside a two-second/24fps composition would lose its endpoint, so the source gate blocks it. The example supplies a longer composition.

## H2-003 — Applied, frame-driven motion

Files: `animation_behavior.py`, `animation_track_compiler.py`.

Supported track actions are enter, exit, reveal, emphasize, transform and path_follow. They apply opacity, clipPath, scale, translation and/or rotation to a real wrapper, rather than emitting only a progress data attribute. The implementation uses `useCurrentFrame`, fps and deterministic interpolation; it does not use wall-clock timers, randomness, CSS transitions or CSS animation.

Track time is `[start_ms, end_ms)`. Sampling uses `round(start_ms*fps/1000)` and `round(end_ms*fps/1000)-1` so the final included frame reaches the final state. Fewer than two distinct frames is rejected; emphasis additionally requires a sampled visible peak. Easing is explicitly linear or smoothstep. Path following requires pixel coordinates and follows polyline arc length, not equal time per arbitrarily unequal segment. Transform keys and ranges are bounded and no-op or malformed tracks are rejected.

Every track declares the visual properties it owns. Multiple owners of the same persistent property on an element are rejected rather than silently overriding or compounding. One explicit neutral enter(0→1) then exit(1→0) non-overlapping pair is allowed. Different property tracks may compose. Unsupported specialized camera/morph/trace/simulation-state actions remain blocked by this path; their independent legacy modules are not silently assumed to be production-integrated.

Motion can still move content outside its original normalized box or composition. H2 does not certify collision-free layout or safely admit every geometric transform. Browser fixtures intentionally use bounded paths/boxes, and a broader frame-aware motion-envelope gate remains H3 work.

## H2-004 — Declared geographic projection

Files: `map_geometry.py`, `map_compiler.py`.

Normalized inline coordinates remain a separate contract. Geographic input requires `crs: EPSG:4326`, an explicit projection kind, `axis_order: lon_lat`, an ordered regional extent, and attribution. The axis order is deliberately declared, not guessed from the CRS string.

Supported projections are spherical Web Mercator and equirectangular with standard parallel zero. Both use radius 6,378,137 metres. Web Mercator computes x=R*lambda and y=R*asinh(tan(phi)); equirectangular computes x=R*lambda and y=R*phi. Mapping to the viewport preserves aspect ratio with isotropic scale. Original, projected and pixel coordinates, the projection and source identity are retained. Independent tests compare these calculations with installed PROJ via pyproj, as well as fixed known points. Two actual browser map fixtures show different geometry under the two declared projections.

Inline route, point and simple closed polygon layers are rendered, up to six layers, with labels and attribution. Unknown/raster layers, malformed coordinates, outside-extent data, duplicate route points, invalid/self-intersecting polygons and unbound layer source references are rejected. Geographic latitudes outside Web Mercator's declared cutoff are errors, not silently clipped. Antimeridian crossings are explicitly unsupported, not drawn as misleading across-world straight lines. There are no fetched tiles, invented base maps, geodesic routing or distance/area accuracy claims.

## H2-005 — Adoption, negative guards and evidence

Files: `scene_behavior_qa.py`, `qa_scene_compile.py`, `capability_fallback_qa.py`, `qa_common.py`; scripts `compile_scene_checked.py`, `validate_checked_remotion.py`, `validate_comp_h2_browser.py`.

All four behavior families feed the existing checked source-publication path. Element source is rederived and compared with governed emitters; animation conflicts, frame quantization, simulation coverage/aliasing and layer provenance have explicit ERROR findings. `src/bie-behavior-contracts.json` records the contracts and remains inside the byte/hash-bound source manifest. Source/sidecar tampering blocks revalidation. A source ERROR may retain a throwing diagnostic stub for mapping, but publication of the entire scene is refused.

Mathtext emits useful multiline failures. H2 found that these could themselves break the strict QA finding contract. `diagnostic_message` escapes control characters at the receipt boundary, preserving the message without relaxing the strict finding validator. Unsupported math now produces a blocked receipt rather than a QA-path crash. The exact error remains available as a safe literal diagnostic stub.

**There are separate evidence levels:**

1. Actual Python code, TypeScript parser/transpiler and strict tsc with labelled ambient dependency declaration doubles.
2. Actual generated component functions executed using explicit React/Remotion hook doubles, compared with independent numeric expectations.
3. Actual Chromium painting of those emitted host-element trees using a clearly labelled test bridge. This includes screenshots, DOM bounds, mathematical layout, marker movement and style changes.
4. Full installed pinned React/Remotion project compile, real composition discovery, actual smoke/full Remotion render, complete-scene frame inspection and real-book acceptance. These remain blocked/not run here.

Level 3 is **not** Level 4. The component bridge is not real React or Remotion, and not a multi-tenant execution sandbox. The unchanged real render API still demands checked source and full-project typechecking before rendering. No successful actual Remotion execution or full generated dependency compile is claimed.

## Provenance and frozen regression

`lineage/hardening_h1/ORIGINAL_MEMBER_HASHES.json` inventories every original H1 member. Every deliberately changed original is copied byte-for-byte below that lineage directory. Existing earlier lineage is preserved. Original `fixtures/comp_qa_009` and `fixtures/comp_h1` corpora and baselines are unchanged. A snapshot of actual historical H1 component output is kept in `fixtures/comp_h2/historical_h1_behavior_results.json`. Old defective raw typesetting and metadata animation remain visible and testable.

The H2 base corpus keeps the **same 19 source documents**, with development-reviewed versioned expectations: supported LaTeX and reveal now pass, unknown simulations and undeclared projection now reject with explicit contract diagnostics. This is 15 positive / 4 negative cases. The extended corpus has 59 synthetic cases across 10 domains: 35 positive / 24 expected rejections. It does not assert real-book validation or comprehensive domain support.

`build_comp_h2_corpus.py` is an explicit development baseline command. It has predeclared expected outcomes, asserts exact diagnostics and never runs automatically during regression. The benchmark cannot update its own goldens. New development baselines do not imply user, subject-expert, learner or product approval.

## Reproduction and requirements

Run from the extracted cumulative root. Python, Node, the actual TypeScript CLI, FFmpeg/ffprobe and Chromium are external tools. Install the pinned `requirements-comp-h2.txt` for the Python typesetter and `requirements-comp-h2-test.txt` for independent test/browser dependencies. Native browser executable must already be installed or supplied explicitly; the harness does not fetch it. No font binaries are included.

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
python scripts/run_compiler_qa.py --output /tmp/bie-h2-new-benchmark --runs 3
python scripts/validate_comp_h2_browser.py --output /tmp/bie-h2-new-browser --chromium /usr/bin/chromium
python scripts/compile_scene_checked.py examples/comp_h2/combined_technical_scene.json /tmp/bie-h2-project
python scripts/validate_checked_remotion.py /tmp/bie-h2-project
# Optional operator-authorized install, in a trusted environment with registry access:
python scripts/validate_checked_remotion.py /tmp/bie-h2-project --install --browser /absolute/path/to/chromium
```

Use new destinations. Exit 2 on the benchmark means expected source outcomes match but full positive compiles are not verified. It is not a rendering pass. The browser component harness exits zero only for its explicitly scoped paint checks. The checked real-render harness blocks at the first unmet required gate.

## Primary documentation

API references support implementation intent; they are not local execution evidence.

- Matplotlib Mathtext API: https://matplotlib.org/stable/api/mathtext_api.html
- Remotion frame hook: https://www.remotion.dev/docs/use-current-frame
- Remotion interpolation: https://www.remotion.dev/docs/interpolate
- PROJ Web Mercator: https://proj.org/en/stable/operations/projections/webmerc.html
- PROJ equirectangular: https://proj.org/en/stable/operations/projections/eqc.html
- MathML Core: https://www.w3.org/TR/mathml-core/
