# Evaluation Implementation Plan

This task establishes the benchmark contract, registry and deterministic aggregator. It does NOT claim that all underlying evaluators exist yet.

Next evaluator families should be implemented as separate atomic tasks:
1. source-grounding evaluator
2. semantic/factual evaluator
3. prerequisite/reasoning evaluator
4. mathematical verifier
5. causal/process verifier
6. pedagogical rubric evaluator
7. representation-fitness evaluator
8. Remotion compile evaluator
9. render evidence collector
10. rendered-frame evaluator
11. Game IR validator
12. game runtime interaction evaluator
13. game-learning alignment evaluator
14. reproducibility/regression evaluator

The benchmark runner should consume evidence artifacts from those evaluators, never scrape informal logs.
