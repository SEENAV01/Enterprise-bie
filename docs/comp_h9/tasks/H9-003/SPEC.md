# BIE-COMP-H9-003 — Source-target-following highlights

## Governing finding
H8 live declared-consumer inventory, consolidated H3-R02. This is an audit-derived task, not a renumbered original-roadmap item.

## Producer / consumer implementation
Outline, fill, spotlight and underline bind to actual source elements and every frame of their supported transformed bounds. H6 visible/opacity states are respected; random-access evaluation does not depend on seek order. Shared source and reasoning references are enforced.

Implementation: `app/bie/compiler/highlight_compiler.py`. The existing DSL registry and original builders are not replaced.

## Bounded contract and non-claims
Conservative transformed element envelopes, not per-glyph contour masks. Separate tracks on the highlight itself are rejected until composition rules are explicit. Target reveal clipping is not exact-ink localization. A highlight remains an intentional overlay, not an occlusion exemption for other elements.

## Reproduce
Restore the complete H9 integrated workspace, or all five ordered H9 deltas from the exact H8 baseline. Intermediate delta stages are source assembly only, not runnable releases.

```bash
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h9_003 -v
```

Suite discovery: 20 tests. Execution evidence is `TEST_RESULT.txt`; final extracted-package verification is external and bound to the archive SHA256. `accepted` remains false.
