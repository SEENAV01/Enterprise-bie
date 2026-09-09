# Integration Plan — Reasoning Layer

## Placement
The enterprise canonical flow becomes:

Document/Knowledge/Prerequisite artifacts
→ Reasoning Decision artifacts
→ Pedagogy / Director / Visual / Animation / Game plans
→ IR/compiler paths.

## Compatibility migration
Current `lesson_planner.py`, `script_compiler.py`, `scene_dsl.py` and `game_generator.py` should not yet be deleted. First introduce adapters that consume ReasoningDecision artifacts while preserving characterization tests. Then replace template assumptions one subsystem at a time.

## Initial decision sequence for a concept
1. prerequisite_order
2. teaching_order
3. misconception_resolution
4. mathematical_derivation or causal_explanation as applicable
5. representation_selection
6. visual_strategy
7. simulation_strategy where useful
8. animation_strategy
9. assessment_strategy
10. game_revision_strategy

Not every concept requires every decision type. A capability selector decides which reasoning operations are applicable.

## QA
Reasoning QA must later validate:
- evidence sufficiency
- contradiction handling
- constraint compliance
- confidence calibration
- downstream consistency
- multi-domain generality
