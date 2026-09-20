# BIE-COMP-H7-006 — Paint/visibility QA

Parent: BIE-COMP-H6-005. Finding: R01.

## Required behavior
Exhaustive source/frame identity, text contrast/occlusion/clip diagnostics, font and visual checks, explicit unsupported-case blockers and measured test fixtures. Installed Fontconfig/FreeType glyph coverage for declared system stacks, vector-ink envelopes and opaque-overlay tests; not universal raster segmentation or shaping/teaching assessment.

## Execution and boundaries
This task's implementation is part of the cumulative H7 integration. Restore all eight ordered deltas before executing task suites; intermediate delta trees are assembly states, not standalone runnable applications.

```bash
PYTHONPATH=app:. python -m unittest tests.compiler.test_comp_h7_006 -v
```

Targeted suite: 35 tests. Full release/package evidence is externally bound to the final integrated ZIP. Real Remotion and browser sandbox execution remain blocked; the local browser bridge has explicit API doubles and cannot authorize a production render. See `docs/COMP_H7_REAUDIT.md` for exact unclosed broader findings. Product accepted: false.

## Failure and traceability
Invalid contracts, missing provenance, modified dependencies/assets/source, unsupported types, resource violations and incomplete evidence fail closed in the relevant path. Fail-closed validation does not count as implementing unsupported capability. All modified original files are in lineage.
