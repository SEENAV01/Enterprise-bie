# BIE-COMP-H9-005 — Adoption, coverage and verified delivery

## Governing finding
H8 live declared-consumer inventory, consolidated H3-R02. This is an audit-derived task, not a renumbered original-roadmap item.

## Producer / consumer implementation
Adopts all three emitters and seven actions in existing checked compilation, source maps, conflict/layout sampling, source publication and revalidation. Coverage is computed from live registry and dispatch; missing dispatch still fails closed if a consumer is removed.

Implementation: `app/bie/compiler/qa_scene_compile.py and existing motion, capability, coverage and reduced-motion paths`. The existing DSL registry and original builders are not replaced.

## Bounded contract and non-claims
18/18 and 16/16 are name-level dispatch coverage, not unrestricted behavior coverage or product acceptance. Strict local TypeScript tests use explicit declarations. Real React/Remotion dependencies and actual renders remain separate required gates.

## Reproduce
Restore the complete H9 integrated workspace, or all five ordered H9 deltas from the exact H8 baseline. Intermediate delta stages are source assembly only, not runnable releases.

```bash
PYTHONPATH=app:. PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.compiler.test_comp_h9_005 -v
```

Suite discovery: 18 tests. Execution evidence is `TEST_RESULT.txt`; final extracted-package verification is external and bound to the archive SHA256. `accepted` remains false.
