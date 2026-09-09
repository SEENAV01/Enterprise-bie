# BIE-DSL-CORE-001 — Universal Scene IR Semantic Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Replace the current fixed presentation-layout assumption with a framework-neutral semantic intermediate representation capable of expressing concept-appropriate educational scenes before Remotion code exists.

Scene IR describes WHAT must appear, WHY it appears, WHEN it appears, HOW it behaves semantically, and WHAT learning/evidence decision it serves. Remotion/React/CSS implementation details belong to the compiler.

## Design principles
1. No mandatory five-pane or other universal layout.
2. A scene may use diagrams, equations, graphs, simulations, maps, timelines, text, images/video, 2D/3D objects, annotations, highlights, camera instructions, audio and interactions as required.
3. Every learning-relevant element links to a semantic purpose and/or reasoning decision.
4. Time is represented independently from FPS so compilers may target different render settings.
5. Spatial intent supports normalized coordinates plus constraints; compilers solve final pixels.
6. Animation is semantic: enter, exit, transform, emphasize, trace, reveal, morph, camera, simulation-state etc.
7. Assets carry provenance/rights references.
8. Scene IR is versioned and framework-neutral.
9. Unsupported compiler capabilities fail explicitly or trigger a planned fallback; they cannot silently disappear.
10. QA validates semantics, temporal consistency, references, constraints and accessibility before code generation.

## Core hierarchy
SceneDocument
→ Scene
→ Layer
→ Element
→ semantic content / spatial intent / temporal interval / animation tracks / interaction bindings.

## Element kinds
text, equation, shape, vector, diagram, graph, chart, map, timeline, image, video, audio_visualizer, simulation, model_2d, model_3d, annotation, callout, highlight, particle_system, custom_component.

The taxonomy is extensible through namespaced custom components; core schemas remain stable.

## Educational semantics
Each element may carry:
- learning_objective_refs
- concept_refs
- reasoning_decision_refs
- source_artifact_refs
- semantic_role
- accessibility label/description.

## Spatial model
Normalized canvas coordinates 0..1 are allowed as intent, but elements may instead use anchors/relationships/constraints. Layout engines may solve final geometry. Hard-coded pixel placement is not required.

## Temporal model
Times are seconds from scene start. start >= 0, end > start. Animation intervals must lie within element/scene lifetimes.

## Compiler boundary
Scene IR contains no JSX, CSS, Remotion hooks, React components or provider prompts. The Remotion compiler translates supported semantic primitives into implementation.
