# Canonical Pipeline Migration Plan

## Rule: strangler migration, not big-bang rewrite
The existing pipeline remains executable while enterprise stages are introduced behind typed adapters.

### Wave 1 — contracts and state
- integrate ArtifactEnvelope
- introduce RunContext
- introduce enterprise execution graph
- wrap current stage outputs without changing behavior
- characterize existing tests

### Wave 2 — missing intelligence
- introduce REASONING stage
- split concept/prerequisite responsibilities
- introduce provider-neutral model/tool gateway later
- make pedagogy consume reasoning artifacts

### Wave 3 — directing and universal visual path
- replace fixed script compiler with Director Plan
- add Visual Plan
- add Animation Plan
- replace fixed Scene DSL with Scene IR
- retain legacy layout only as optional component strategy

### Wave 4 — game path
- add Game Director
- emit Game IR
- compile Game IR through mechanic registry
- remove title-keyword branching

### Wave 5 — actual execution evidence
- real TypeScript/Remotion compile
- real video render
- rendered-frame QA
- real game build/runtime interaction tests

### Wave 6 — release and benchmark
- evidence-backed ReleaseEvaluator
- golden benchmark runner
- regression/reproducibility evidence
- remove M301 synthetic production certification.

No legacy module is deleted until its enterprise replacement passes characterization + integration + golden tests.
