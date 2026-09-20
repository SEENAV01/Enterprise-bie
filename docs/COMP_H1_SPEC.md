# COMP Hardening H1 — specification and contract boundaries

Delivery sequence 10. Audited parent: original COMP Batch 009, QA-005. This is an additive hardening phase under the original BIE architecture, not a restart, replacement engine, or original-roadmap renumbering. Governed tasks: `governance/COMP_H1_TASK_REGISTRY.json`. The product remains NOT ACCEPTED and COMP remains IN PROGRESS.

## H1-001 — literal text safety

Implementations: `hardening_contracts.py`, `text_compiler.py`, `annotation_callout_compiler.py` under `app/bie/compiler`.

Text, annotation and callout bodies use a JSON string expression rather than raw JSX children. Quotes, braces, markup, template-looking text, ampersands, newlines, bidi/multilingual text and code examples remain literal text. Unpaired surrogate inputs fail. Literal encoding is bounded to 100,000 characters and inherited lexical lint-trigger punctuation is escaped inside the JSON string without altering displayed characters. Accessibility text also uses bounded literal encoding. Required provenance, element identity and existing wrapper interfaces remain intact.

Tests inspect emitted source and execute real TypeScript-transpiled components using an explicitly labelled test JSX runtime. These are NOT actual React/Remotion/browser renders or a proof of an exhaustive security sandbox. Negative literal Math.random examples are made to throw if executed, so passing the round-trip test is not just an assertion about source spelling.

## H1-002 — native chart dispatch and signed geometry

Implementations: `chart_geometry.py`, `chart_compiler.py`.

Support bar, line, area, scatter and pie as distinct native SVG geometries. No silent bar fallback. Linear Cartesian axes include zero and signs are preserved: negative bars extend below the zero baseline, positives above; all-negative/all-zero/mixed datasets have finite governed geometry. Category/index and value associations remain stable. Area closes to the zero baseline, line uses polyline, scatter consumes explicit numeric `x_values` and preserves numeric spacing. Pie rejects signed values and zero totals; a single positive slice uses two arcs to represent the full circle. Zero values are retained in the data/legend rather than manufactured into nonzero slices.

Inputs are bounded to 2,000 items; categories to 256 characters; finite numbers have magnitude <=1e100. Booleans/coerced strings and integers outside the exact JavaScript integer range are rejected. Only the declared properties are consumed; extra fields such as a requested log scale are blocked. Label sets above 12 entries or categories longer than 30 characters emit an unreviewed-layout warning that the checked source path blocks rather than claiming legibility.

Local SVG coordinate generation and the generated TSX geometry are tested. This is not evidence of final frame appearance. Subpixel values/extreme dynamic ranges, contrast, dense labels, multi-series/scales, multiple scene layouts and cross-platform raster behavior require further visual-contract hardening and actual frame inspection. Unsupported features must not be described as implemented.

## H1-003 — dimensional vector contract

Implementations: `vector_geometry.py`, `vector_compiler.py`.

2D vectors retain a Cartesian x-right/y-up convention. A 3D vector requires an explicit `orthographic_matrix` projection with two three-component orthonormal rows and a nonempty view label. The implementation computes both projected coordinates from all three source components, displays original components/units and view identity, and refuses a projection that hides a nonzero vector. No undeclared camera, auto-flattening, implied shared scale or 3D simulation is invented. Zero vectors render as a point; each vector's finite viewport scale is explicitly labelled as individual, not a comparable magnitude scale across different vectors.

Orthonormal validation tolerance is 1e-9. A projected/source magnitude ratio below 1e-10 for a nonzero vector is blocked. Nonfinite or underflowed view scales fail. Unknown fields and unconsumed origins are blocked. Full 3D camera/occlusion and shared scene-scale contracts remain separate work.

## H1-004 — normalized 2D topology

Implementations: `model2d_geometry.py`, `model2d_compiler.py`.

The implemented contract is a normalized 2D, undirected, simple graph: at least two unique vertices with finite x/y in [0,1], each edge a pair of distinct valid integer indices. Reject missing/invalid indices, booleans, non-integer indices, malformed edges, duplicate undirected edges, self loops, duplicate vertices and unknown fields. Directed or multigraph semantics are not silently dropped. Coordinates map to a padded x-right/y-down SVG viewport. Isolated vertices are drawn explicitly, including when no edges exist.

Invalid input fails before a runnable element is published. The diagnostic assembler may retain a throwing stub with an ERROR finding to preserve diagnostics/source maps; the checked publisher must refuse the entire erroneous scene. Such a stub is never a functional fallback or accepted output.

## H1-005 — checked publication and real render entry enforcement

Implementation: `checked_scene_compile.py`. Entry points: `scripts/compile_scene_checked.py`, `scripts/run_comp_render.py`, `render_runtime.py`, `scripts/validate_checked_remotion.py`.

Wrap the existing assembler, capability/source-contract checks and real installed TypeScript parser/AST. Inspect output of the governed H1 emitters by recomputation, not metadata assertions. Publication requires no source ERROR and an actual parser PASS; it creates a fresh staged workspace, forbids overwriting an existing destination, writes exact source/codegen metadata and a bounded input/target/receipt envelope. A source PASS is deliberately not a full dependency compile or product approval.

Before real rendering, rederive source from the bound Scene IR/target, reapply guards, compare source and codegen manifest, reject tampering/uninspected source/config/assets/symlinks, bind composition ID/dimensions/fps/duration/entrypoint to the source, and reject unbound runtime props. The CLI AND underlying real-run API enforce this gate. Actual pinned-project typechecking, including source-program coverage, must also pass before Remotion launches. Test-double render branches remain explicitly labelled and cannot become real-render evidence.

The node_modules dependency tree is outside the rederived source receipt. Dependency versions/program coverage are checked by the separate full-typecheck gate, not by a cryptographic software-supply-chain attestation. This is a trusted-local-workspace execution contract, not hostile multi-tenant isolation; concurrent file races and arbitrary malicious dependency execution need OS/container policy and later security acceptance.

The new `validate_checked_remotion.py` is the compatible opt-in real execution harness for checked Scene-IR projects. It requires source validation, optionally installs dependencies only with `--install`, then real strict compilation, real CLI composition ID discovery, smoke/full render, media probing and artifact/log verification. It never marks visual-frame inspection or book/learning acceptance as performed. The retained Batch 008 technical-fixture generator and legacy validation script are historical diagnostic paths, NOT eligible for the new checked rendering path; do not remove the gate to run them.

## Lineage, versioning and regression

All Batch 009 original ZIP members are listed in `lineage/batch_009/ORIGINAL_MEMBER_HASHES.json`. Every changed parent member is preserved at its original relative path below that lineage directory. Originals are also retained in the unchanged parent master backup. No earlier ZIP is overwritten. Modified inherited tests have intentional behavior changes, not deleted coverage: the prior emitter outputs are frozen in `fixtures/comp_h1/historical_emitter_results.json` and still passed through the defect detectors.

The old 19-case corpus and goldens in `fixtures/comp_qa_009` are unchanged. `fixtures/comp_h1/corpus.json` keeps the SAME 19 source documents with versioned expectations and new explicit test-author baselines. The compiler identity is `1.1.0-comp-h1`. `extended_corpus.json` adds 14 synthetic technical cases for a total 33: 20 positive source cases and 13 expected rejections in 10 domains. New goldens are a reviewed development expectation, not user, textbook expert or product approval. No benchmark automatically rebases goldens.

In addition to the 128 new atomic tests, integration tests cover lineage, unchanged inputs, checked CLI entry, exact source/render bindings, unsupported semantic fields and ambient-typechecked native components. The ambient run uses real TypeScript with explicit dependency declaration TEST DOUBLES; it is not a successful compile of pinned React/Remotion APIs.

## Reproduction

From the extracted cumulative root, with Python, Node, TypeScript and the inherited FFmpeg/ffprobe tools available:

```bash
PYTHONPATH=app:. python -m unittest discover -s tests -v
python scripts/run_compiler_qa.py --output /tmp/bie-comp-h1-new-benchmark
python scripts/compile_scene_checked.py examples/comp_h1/signed_chart_scene.json /tmp/bie-h1-project
python scripts/validate_checked_remotion.py /tmp/bie-h1-project
# Explicit operator permission for network dependency installation:
python scripts/validate_checked_remotion.py /tmp/bie-h1-project --install --browser /absolute/path/to/chromium
```

Use fresh destination/run paths. The compiler/source benchmark performs no npm installation or GitHub write. Benchmark exit 2 means expectations matched but full compile evidence remains incomplete. Checked-validation exit 2 means a required gate blocked/failed. Successful technical source or execution stages never grant educational/product acceptance.

## Evidence scope and open gates

The local environment has TypeScript 5.8.3, but unchanged generated packages request 5.9.3, React 19.0.0 and Remotion 4.0.506. The npm probe returned EAI_AGAIN. Real AST, test-runtime execution, limited ambient strict checks and inherited FFmpeg technical tests are separate from the missing full pinned-project compile, real CLI discovery, actual Remotion smoke/full render and frame inspection. Real books, autonomous production orchestration, playable games, domain-expert/learner validation and final acceptance remain open.

Remaining original defect work: equation typesetting (F05), executable simulation semantics (F06), real frame-driven animation rather than metadata (F07), correct geographic projection (F08). Additional residual review items are recorded in COMP_H1_REAUDIT.md. No automatic section exit is permitted.

## Primary API documentation consulted

- React JSX expression/literal boundaries: https://react.dev/learn/javascript-in-jsx-with-curly-braces
- TypeScript strict option: https://www.typescriptlang.org/tsconfig/strict.html
- Remotion rendering CLI: https://www.remotion.dev/docs/cli/render

Documentation establishes API intent, not that this workspace successfully rendered. Local execution evidence is stored separately.
