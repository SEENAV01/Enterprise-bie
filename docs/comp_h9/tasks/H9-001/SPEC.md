# BIE-COMP-H9-001 — Seven original shape kinds

## Governing finding
H8 live declared-consumer inventory, consolidated H3-R02. This is an audit-derived task, not a renumbered original-roadmap item.

## Producer / consumer implementation
Source rectangle, circle, ellipse, line, polygon, polyline and arrow geometry becomes SVG. Coordinates, view box and safe paint are explicit; arrowheads retain direction, open paths remain open. Required alt and provenance remain bound.

Implementation: `app/bie/compiler/primitive_geometry.py; app/bie/compiler/shape_compiler.py`. The existing DSL registry and original builders are not replaced.

## Bounded contract and non-claims
No arbitrary path DSL, implicit coordinate inference, CSS/URL input, self-intersecting polygons or silent clipping. Named/RGB colors; alpha is an explicit opacity field. A source geometry check is not pixel/educational acceptance.

## Reproduce
Restore the complete H9 integrated workspace, or all five ordered H9 deltas from the exact H8 baseline. Intermediate delta stages are source assembly only, not runnable releases.

```bash
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h9_001 -v
```

Suite discovery: 26 tests. Execution evidence is `TEST_RESULT.txt`; final extracted-package verification is external and bound to the archive SHA256. `accepted` remains false.
