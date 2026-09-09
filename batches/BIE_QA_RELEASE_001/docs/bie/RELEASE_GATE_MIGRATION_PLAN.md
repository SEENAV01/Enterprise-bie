# Release-Gate Migration Plan

## Current code impact
- `app/bie/canonical_pipeline.py`: stop assigning `status: SUCCESS` immediately after code generation.
- `app/bie/m301_real_execution.py`: stop using layout pass + manifest status as production certification.
- `app/bie/EXECUTION_MANIFEST.json`: becomes a legacy/generated artifact, not an authoritative release certificate.

## Replacement sequence
1. Add evidence artifact producers for lineage/source/semantic/pedagogy/etc.
2. Add real Remotion compile command evidence.
3. Add real render-job evidence + output hash.
4. Add rendered-frame inspection evidence.
5. Add game build evidence.
6. Add game runtime/interaction evidence.
7. Add regression/reproducibility evidence.
8. Evaluate ReleasePolicy deterministically.
9. Emit `release.manifest` only from ReleaseDecision.
10. Preserve all historical FAIL evidence; repairs create new evidence.

## Important
This task defines release semantics. It does not pretend that all listed evaluators are implemented yet. Each evaluator becomes its own downstream atomic task.
