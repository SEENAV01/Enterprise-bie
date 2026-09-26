# BIE-GAME-COMP-004 — state machine compiler

## Purpose
Compile one governed GAME capability into a deterministic, content-addressed runtime artifact while preserving studio-grade interaction semantics and provenance.

## Capability-specific invariants
- typed state schema
- bounds/units/roles preserved
- deterministic reset policy
- runtime state type emitted

## Cross-cutting enterprise invariants
- Batch 01–05 source identity must remain unchanged.
- generated artifacts are path-confined, hashed and provenance-bound.
- no `eval`, `exec`, `new Function`, dynamic import fallback or remote-network dependency.
- compiler output must remain deterministic under identical input/profile.
- studio semantics (stateful interaction, semantic visuals, pedagogical motion, accessibility) may not be flattened into slide/card defaults.
- missing policies, text, assets, provenance or unsafe telemetry fail closed.
- `product_accepted=false`.

## Source
`bie/game_engine/compiler_engine/state_machine.py`

## Tests
`tests/compiler_engine/test_bie_game_comp_004.py` plus compiler architecture/security/typecheck/browser suites.

## Acceptance boundary
Atomic implementation evidence only. No section/product acceptance is implied.
