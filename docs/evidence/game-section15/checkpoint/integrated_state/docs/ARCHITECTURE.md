# Batch 02 Strategy Engine Architecture

The Strategy Engine is additive over Batch 01 GAME DSL/Core. Batch 01 source files are byte-identical and validated by dependency binding.

## Layers
1. `contracts.py` — typed strategy signals, runtime capabilities, score components, assessments, decisions and policies.
2. `common.py` — only cross-strategy primitives: weighted score, confidence, runtime blockers, canonical assessment construction.
3. Nine independent evaluators — retrieval, manipulation, simulation, prediction, diagnostic, timeline, map, equation and causal-system. Each owns its own eligibility and scoring semantics.
4. `selector.py` — runs every evaluator, ranks deterministically, applies score/confidence/runtime policy and explicitly abstains on ambiguity/no eligibility.

## Studio-quality boundary
A strategy is not a label. Every eligible assessment emits downstream design requirements for semantic visuals, interaction, motion/camera/accessibility and evidence boundaries. The selector never falls back to a slide deck or keyword-match strategy.

## Fail-closed rules
- unsupported/missing evidence blocks the affected strategy;
- missing runtime capabilities block the affected strategy;
- near-tied top strategies abstain rather than silently choose;
- simulation cannot claim truth outside declared model scope;
- causal strategy rejects unsupported/cyclic causal structures;
- equation strategy requires symbolic structure and equivalence invariant;
- product acceptance remains false.
