# BIE-COMP-H9-002 — Explicit diagram nodes and relations

## Governing finding
H8 live declared-consumer inventory, consolidated H3-R02. This is an audit-derived task, not a renumbered original-roadmap item.

## Producer / consumer implementation
Original diagram nodes/edges are consumed with declared layout, labels and direction. Relations attach to node boundaries. Isolated nodes remain present. Unknown endpoints, duplicate relations and unrelated-node occlusion reject rather than invent information.

Implementation: `app/bie/compiler/diagram_compiler.py; app/bie/scene_ir/diagram_element.py`. The existing DSL registry and original builders are not replaced.

## Bounded contract and non-claims
Straight-edge, explicitly positioned diagrams only. Automatic graph layout, arbitrary curved routing and self loops need different explicit contracts. Reading/teaching quality is not established by preserving nodes and edges.

## Reproduce
Restore the complete H9 integrated workspace, or all five ordered H9 deltas from the exact H8 baseline. Intermediate delta stages are source assembly only, not runnable releases.

```bash
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h9_002 -v
```

Suite discovery: 24 tests. Execution evidence is `TEST_RESULT.txt`; final extracted-package verification is external and bound to the archive SHA256. `accepted` remains false.
