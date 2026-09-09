# BIE-INFRA-INTEGRATION-001 — Enterprise Contract Integration

Status: IMPLEMENTED + CONTRACT TESTED

## Objective
Integrate the enterprise contracts into one canonical execution graph without pretending that legacy M001→M301 modules have already been replaced.

## Canonical enterprise flow

SOURCE
→ DOCUMENT_INTELLIGENCE
→ KNOWLEDGE
→ PREREQUISITE
→ REASONING
→ PEDAGOGY
→ DIRECTOR
→ VISUAL
→ ANIMATION
→ SCENE_IR
→ VIDEO_CODE
→ VIDEO_COMPILE
→ VIDEO_RENDER
→ VIDEO_QA

and, from the same grounded learning state:

REASONING / PEDAGOGY
→ GAME_DIRECTOR
→ GAME_IR
→ GAME_CODE
→ GAME_BUILD
→ GAME_RUNTIME
→ GAME_QA

Both branches converge:

VIDEO_QA + GAME_QA + LINEAGE + REGRESSION + REPRODUCIBILITY
→ RELEASE_EVALUATION
→ RELEASE_MANIFEST

## Integration invariants
1. No raw source → Remotion code edge.
2. No raw source → game code edge.
3. Scene IR is mandatory before video code generation.
4. Game IR is mandatory before game code generation.
5. Reasoning is mandatory before pedagogy/director/visual/game planning.
6. Every stage consumes and emits typed artifact envelopes.
7. Stage completion is not release success.
8. Release evaluation consumes evidence, not informal logs.
9. Legacy modules may temporarily execute behind adapters but cannot bypass enterprise contracts.
10. Video and game remain two first-class outputs from the same grounded knowledge/reasoning state.

## Legacy mapping
- M001 document ingestion → DOCUMENT_INTELLIGENCE
- M050 concept understanding → KNOWLEDGE + PREREQUISITE
- M100 lesson planning → PEDAGOGY
- M150 script compiler → DIRECTOR
- M200 Scene DSL → VISUAL + ANIMATION + SCENE_IR
- M250 Remotion generator → VIDEO_CODE
- M275 game generator → GAME_DIRECTOR + GAME_IR + GAME_CODE
- M301 execution → RELEASE_EVALUATION

The mapping preserves useful historical work but does not preserve architectural limitations.
