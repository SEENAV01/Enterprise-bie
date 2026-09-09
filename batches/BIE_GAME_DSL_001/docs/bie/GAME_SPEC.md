# BIE-GAME-DSL-001 — Enterprise Game IR Semantic Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Define a framework-neutral Game Intermediate Representation (Game IR) for concept-grounded revision experiences.

Game IR is not quiz JSON. It captures learning intent, mastery targets, misconceptions, mechanics, manipulables, state, rules, challenges, adaptive progression, feedback, scoring, accessibility, telemetry hooks and compiler capability requirements before any specific runtime code is generated.

## Core principles
1. Game generation is first-class and grounded in the same learning model as video.
2. Mechanics are selected because they serve learning objectives, not because a topic keyword matched a hard-coded branch.
3. Game IR contains semantic mechanics and state rules, not framework-specific JavaScript/React/Godot code.
4. Each challenge traces to concept(s), learning objective(s), misconception(s), and reasoning decision(s).
5. Cause-effect rules must be explicit and testable.
6. Adaptive difficulty is represented as policy/conditions, not hidden prompt behavior.
7. Feedback must distinguish correctness, misconception diagnosis, hinting and explanation.
8. Runtime compiler capabilities are explicit; unsupported capabilities fail or invoke declared fallback.
9. Game QA can validate learning coverage, rule consistency, unreachable states, invalid targets, and interaction semantics before runtime generation.
10. Scoring must not substitute for learning correctness.

## Core hierarchy
GameDocument
→ GameExperience
→ Level
→ StateVariable / Manipulable
→ Rule
→ Challenge
→ Feedback
→ Progression/Adaptation.

## Supported mechanic families
- manipulate_parameter
- drag_and_drop
- spatial_arrangement
- sequence_ordering
- classify_sort
- construct_model
- simulation_experiment
- graph_exploration
- timeline_reconstruction
- map_interaction
- equation_balance
- prediction_then_observe
- misconception_trap
- diagnose_error
- branching_scenario
- resource_tradeoff
- matching
- retrieval
- custom_mechanic

## Learning semantics
Each challenge may reference:
- concept_refs
- prerequisite_refs
- learning_objective_refs
- misconception_refs
- reasoning_decision_refs
- source_artifact_refs

## State and rules
StateVariable carries type, domain/range, initial value and optional units.
Rule contains trigger expression, effects, explanation, evidence references and priority.
Compilers may map the semantic rule to a specific runtime engine.

## Challenge contract
A challenge defines:
- prompt/mission
- mechanic
- success condition
- failure/misconception conditions
- allowed actions
- hint ladder
- feedback policy
- mastery contribution
- difficulty metadata.

## Adaptive progression
Adaptation rules may inspect attempts, mastery estimate, misconception flags, latency and hint usage. They may choose easier/harder variants, remedial bridge, replay, or advance.

## Compiler boundary
Game IR contains no DOM, React hooks, Phaser/Godot APIs, or provider prompts. A compiler/runtime adapter consumes validated Game IR.
