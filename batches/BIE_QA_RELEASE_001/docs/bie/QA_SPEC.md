# BIE-QA-RELEASE-001 — Evidence-Backed Enterprise Release Gate Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Prevent false production success. A BIE release can be declared SUCCESS only when required evidence artifacts exist, validate, and cover both teaching-video and revision-game outputs.

This contract replaces generation-only acceptance with evidence-backed release semantics.

## Required release dimensions
A production release policy may require gates in these classes:

1. lineage_integrity
2. source_grounding
3. semantic_correctness
4. prerequisite_correctness
5. pedagogical_correctness
6. mathematical_correctness
7. director_quality
8. visual_quality
9. animation_quality
10. timing_audio_sync
11. code_compile
12. video_render
13. rendered_frame_inspection
14. game_build
15. game_runtime
16. game_learning_alignment
17. accessibility
18. regression
19. reproducibility
20. rights_and_asset_provenance
21. security
22. performance

Not every domain requires all gates; the ReleasePolicy explicitly marks which are REQUIRED, OPTIONAL or NOT_APPLICABLE.

## Evidence model
Each gate is evaluated from one or more immutable evidence records. Evidence includes:
- gate id/type
- status PASS/FAIL/ERROR/SKIPPED
- evaluator identity/version
- artifact refs inspected
- measurements
- threshold/result summary
- evidence artifact refs
- timestamp
- diagnostics
- remediation owner/layer

## Hard invariants
1. REQUIRED gate cannot be SKIPPED.
2. REQUIRED gate must have evidence.
3. Any REQUIRED FAIL or ERROR blocks release.
4. SUCCESS cannot be computed from generated file presence alone.
5. Video release requires actual compile and render evidence where video output is enabled.
6. Game release requires actual build and runtime evidence where game output is enabled.
7. Lineage integrity is always required.
8. Source grounding is always required for teaching/revision content.
9. Evidence must reference the artifacts actually evaluated.
10. Remediation may not downgrade a required gate to optional.
11. A rerun after repair produces new evidence; old failed evidence remains in history.
12. Release decision is deterministic from policy + evidence set.

## Release statuses
- BLOCKED
- READY_FOR_REVIEW
- RELEASE_CANDIDATE
- SUCCESS

SUCCESS is only possible when all required gates PASS and no policy-level review is pending.

## Failure routing
Every failed gate identifies the owning remediation layer, e.g.:
- source/semantic -> BI/KI/RE
- prerequisite -> PR/RE/PED
- pedagogy -> PED
- director -> DIR
- visual -> VIS/DSL
- animation -> ANI/DSL
- compile/render -> COMP/INFRA
- game learning/runtime -> GAME
- lineage/reproducibility/security -> INFRA
- global acceptance -> QA

## Reproducibility
Release evidence should include source hashes, config hash, model/tool policy id, code revision, dependency lock hash, and output artifact hashes. Exact byte-for-byte media reproducibility may be policy-defined when nondeterministic providers are used; semantic/config/code traceability remains mandatory.

## Migration impact
Current `EXECUTION_MANIFEST.json` status field becomes non-authoritative legacy output.
Current `m301_real_execution.py` must later use this evaluator rather than printing production certification from layout/generation success.
