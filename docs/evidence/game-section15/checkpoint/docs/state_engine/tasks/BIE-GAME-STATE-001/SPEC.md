# BIE-GAME-STATE-001 — state-variable model

## Status
Original enterprise-depth implementation for Section 15 Batch 04. Individually traceable inside the cumulative batch.

## Purpose
Typed variable schema, initial immutable snapshot, type/range/enum validation and content-addressed schema identity.

## Inputs
- Batch-01 typed Game IR / StateModel / InteractionContract / safe Expr AST.
- Immutable or caller-owned state values; task code must not mutate upstream objects.
- Provenance-grounded rules/actions already validated by the DSL layer.

## Output contract
Handler: `compile_state_model` in `bie/game_engine/state_engine/state_variables.py`.
All outputs are deterministic for identical governed inputs and keep `product_accepted=false`.

## Algorithmic requirements
- deterministic ordering and content fingerprints
- fail-closed validation
- type-aware state semantics
- no arbitrary Python eval/exec
- immutable before/after state evidence
- stable machine-readable GAME error codes
- compatible with replay/transition receipts and later Mechanics/Compiler layers

## Capability-specific failure modes
- missing/extra state coverage
- wrong scalar type
- numeric bounds
- enum membership

## Verification
Atomic suite: `tests/state_engine/test_state_001_state_variables.py` — 12 tests.
Cumulative checkpoint after this task: 12 STATE task tests PASS.
Cross-cutting transition/replay/invariant/security suites are additionally run at Batch 04 level.

## Acceptance boundary
PASS means implementation evidence only. It does not mean Section 15 accepted, runtime product accepted, real-book E2E accepted, or release authorized.
