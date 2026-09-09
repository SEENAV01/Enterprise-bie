# BIE-INFRA-EVAL-001 — Multi-Domain Golden Benchmark & Evaluation Framework

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Define how BIE proves that it is genuinely capable across different textbook domains rather than succeeding on one demo chapter.

The benchmark framework evaluates the full learning-production stack:
source understanding → knowledge/prerequisite reasoning → pedagogy → director decisions → visual/animation representation → Scene IR → video code/build/render → revision Game IR/build/runtime → QA/release evidence.

## Golden benchmark philosophy
A golden benchmark case is not merely an input PDF and one expected string. It is a versioned evaluation package containing:
- source fixture reference
- domain and concept class
- required source-grounded truths
- prerequisite relationships
- misconception targets
- expected reasoning properties
- pedagogical requirements
- acceptable representation families
- forbidden representations/claims
- required video/runtime evidence
- required game/mastery behaviors
- scoring rubric
- critical hard-fail conditions.

## Required initial domain families
The enterprise benchmark registry must contain representative cases from at least:

1. Physics
   - vector/force reasoning
   - equations and simulation
2. Mathematics
   - symbolic derivation/proof/graph transformation
3. Biology
   - process/system/structure reasoning
4. History / Civics
   - chronology, causality, actors, source sensitivity
5. Geography / Earth Science
   - maps, spatial systems, physical processes

Additional domains may be added without changing the evaluator contract.

## Metric families
The framework supports:

- source_grounding
- factual_semantic_correctness
- concept_coverage
- prerequisite_correctness
- reasoning_validity
- reasoning_evidence_sufficiency
- misconception_handling
- mathematical_correctness
- causal_correctness
- pedagogical_sequence
- explanation_quality
- director_coherence
- representation_fitness
- visual_semantic_alignment
- animation_semantic_alignment
- scene_ir_validity
- video_compile_success
- video_render_success
- rendered_frame_quality
- timing_audio_sync
- game_ir_validity
- game_runtime_success
- game_learning_alignment
- adaptive_revision_quality
- accessibility
- reproducibility
- regression_stability

## Metric semantics
Each metric score is normalized 0..1.

A benchmark case contains:
- weight
- minimum score
- critical flag.

Critical metrics are hard floors. A high average cannot hide a failure in source grounding, math correctness, runtime, etc.

## Case result semantics
Case status:
- PASS
- FAIL
- ERROR

PASS requires:
- no critical metric below its floor
- all mandatory evidence present
- weighted aggregate >= case threshold.

## Suite result semantics
Suite status:
- PASS
- FAIL

PASS requires:
- every required benchmark case PASS
- no domain family below its minimum aggregate
- global weighted score >= suite threshold.

## No single-demo certification
A production/enterprise capability claim must not be based on one Coulomb’s Law, one physics chapter, or one generated render. The benchmark suite is explicitly multi-domain.

## Human + automated evaluation
Metrics may be produced by:
- deterministic validators
- specialist solvers
- rendered-frame checks
- runtime tests
- rubric-based model evaluators
- human expert review
- hybrid adjudication.

The evaluator identity/version and evidence must be stored.

## Golden data governance
Golden expectations are versioned. Changes require:
- reason for change
- reviewer
- benchmark version bump
- regression comparison.

Benchmark changes cannot be silently made merely to improve current scores.
