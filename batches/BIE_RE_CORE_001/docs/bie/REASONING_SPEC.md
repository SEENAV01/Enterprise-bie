# BIE-RE-CORE-001 — Enterprise Reasoning Decision Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
BIE requires an explicit, provider-neutral, auditable reasoning layer between grounded understanding and downstream pedagogy/directing/code generation.

The reasoning layer does not expose or depend on hidden chain-of-thought. It stores concise, structured decision artifacts: what decision was made, what evidence supports it, what alternatives were considered, what constraints applied, how confident BIE is, and what downstream systems may consume the result.

## Required Decision Types
The enterprise contract supports at least:

- prerequisite_order
- teaching_order
- causal_explanation
- mathematical_derivation
- misconception_resolution
- representation_selection
- example_selection
- assessment_strategy
- remediation_strategy
- visual_strategy
- simulation_strategy
- animation_strategy
- game_revision_strategy
- evidence_arbitration
- contradiction_resolution
- uncertainty_resolution

## Reasoning Decision Structure
Every decision includes:

- `decision_id`
- `decision_type`
- `subject_id`
- `question`
- `selected_option`
- `alternatives`
- `evidence_refs`
- `premises`
- `constraints`
- `confidence`
- `uncertainty`
- `rationale_summary`
- `downstream_effects`
- `requires_review`
- `policy_tags`

The decision is itself wrapped in the canonical BIE ArtifactEnvelope.

## Core Invariants
1. A decision affecting teaching, visuals, animation or game behavior MUST reference grounded evidence or an explicitly inferred parent artifact.
2. `confidence` is always 0..1.
3. Material uncertainty must be explicit; it cannot disappear between stages.
4. Alternatives may be empty only when the decision is deterministic or uniquely constrained.
5. A selected option must not silently violate a declared constraint.
6. Critical decisions below the configured confidence threshold must set `requires_review=true` or trigger escalation.
7. Downstream systems consume structured decisions, not provider-specific prose.
8. Decision artifacts are immutable by content and traceable through the canonical lineage envelope.
9. Reasoning QA evaluates decision validity, evidence sufficiency, contradiction handling, confidence calibration and downstream consistency.
10. No reasoning artifact may claim mathematical or causal certainty solely because an LLM produced it.

## Decision Graph
Reasoning decisions may depend on prior reasoning decisions. The graph must be acyclic. This permits explicit chains such as:

source evidence
→ concept interpretation
→ prerequisite order
→ teaching order
→ representation selection
→ visual strategy
→ animation strategy
→ assessment/game strategy

## Confidence and Escalation
Recommended enterprise bands:

- 0.90–1.00: high confidence
- 0.75–0.89: acceptable with normal QA
- 0.50–0.74: review/escalation required for critical decisions
- below 0.50: decision must not automatically drive production

Thresholds are policy-configurable and belong to the Quality Governor, not hard-coded business logic.

## Provider Neutrality
The reasoning contract never requires a specific provider. A deterministic engine, local model, cloud LLM, specialist solver, human reviewer, or hybrid path may produce a valid decision if the artifact contract and QA gates are satisfied.

## Downstream Ownership
- PED consumes prerequisite/teaching/remediation/assessment decisions.
- DIR consumes explanation, narrative and emphasis decisions.
- VIS consumes representation/visual/simulation decisions.
- ANI consumes animation/timing/attention decisions.
- GAME consumes revision/mechanic/mastery decisions.
- QA verifies all of the above and may route failures upstream.
