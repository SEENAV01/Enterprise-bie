# BIE-INFRA-AUDIT-001 — ENTERPRISE REPOSITORY GAP AUDIT

Status: QA_VERIFIED (classification audit complete; implementation actions are not yet performed)

## Executive conclusion
The current repository contains valuable implementation seeds across ingestion, concept/prerequisite modeling, graph/math/layout engines, Remotion generation, game generation, testing and infrastructure. It must **not** be discarded wholesale. However, the current canonical pipeline is not the final enterprise architecture: it directly wires ingestion -> concept understanding -> fixed lesson planning -> template script -> fixed Scene DSL -> code generation -> game generation -> SUCCESS manifest.

The enterprise migration therefore uses **preserve-the-good, replace-the-assumptions**:
- deterministic primitives and registries are generally KEEP+REFACTOR;
- fixed pedagogy/director/visual/game template layers are REPLACE;
- orchestration, contracts, compiler, QA and infrastructure are REFACTOR into typed/versioned enterprise subsystems;
- generated artifacts/caches are removed from normal source control;
- production success becomes evidence-backed.

## Critical blockers before enterprise implementation can be called real
1. No authoritative provider-neutral reasoning artifact/state between concept understanding and pedagogy.
2. Fixed pedagogical phases and scripted personas/sequence encode decisions that BIE must autonomously make.
3. Scene DSL is a fixed five-pane presentation, not universal visual/animation IR.
4. Video generator emits code/layout but the canonical success path does not require actual Remotion compile/render/frame inspection.
5. Game generation branches by concept-title keywords and falls back to generic physics, so it is not domain-general revision intelligence.
6. Current acceptance runner uses a synthetic in-memory textbook and can print CERTIFIED PRODUCTION READY based mainly on manifest/layout checks.
7. Artifact lineage, versioned contracts, benchmark evidence, reproducibility and upstream failure routing are not yet first-class.
8. Repository hygiene includes generated output, Python/pytest caches and should be normalized before enterprise CI.
9. Provider-specific model integration must move behind a model/tool gateway.
10. Monolithic service/runtime infrastructure must be decomposed around jobs, artifacts, orchestration and evidence.

## Migration rule
Do not rewrite everything in one pass. Each row in REPOSITORY_CLASSIFICATION.csv becomes one or more atomic migration tasks with compatibility tests. Existing useful behavior is captured by characterization tests before replacement.

## Next dependency-valid task
BIE-INFRA-CONTRACT-001 — define the Canonical Artifact Envelope + lineage/version contract used by every BIE stage. This must precede the enterprise Reasoning Artifact, Scene IR, Game IR and Release Gate implementation.
