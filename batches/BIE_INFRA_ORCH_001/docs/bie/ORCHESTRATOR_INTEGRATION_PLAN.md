# Orchestrator Integration Plan

1. Build StageDefinition registry from the canonical enterprise graph.
2. Wrap legacy modules with temporary executor adapters.
3. Wrap every stage output in ArtifactEnvelope.
4. Replace direct object passing with ArtifactResolver interfaces.
5. Persist RunStateMachine after every transition.
6. Route failures to remediation owners.
7. Keep the legacy canonical pipeline behind a feature flag until characterization tests pass.
8. Do not allow adapters to bypass Scene IR, Game IR, evidence or release gates.
