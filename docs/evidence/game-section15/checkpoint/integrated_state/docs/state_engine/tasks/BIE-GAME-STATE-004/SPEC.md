# BIE-GAME-STATE-004 — cause-effect effects

## Status
Original enterprise-depth implementation for Section 15 Batch 04. Individually traceable inside the cumulative batch.

## Purpose
Apply typed state effects without mutating input, preserving integer/boolean semantics, bounds and ordered deltas.

## Inputs
- Batch-01 typed Game IR / StateModel / InteractionContract / safe Expr AST.
- Immutable or caller-owned state values; task code must not mutate upstream objects.
- Provenance-grounded rules/actions already validated by the DSL layer.

## Output contract
Handler: `apply_effect / apply_effects` in `bie/game_engine/state_engine/effects.py`.
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
- divide by zero
- numeric range escape
- integer preservation
- toggle non-boolean
- no-op delta

## Verification
Atomic suite: `tests/state_engine/test_state_004_effects.py` — 14 tests.
Cumulative checkpoint after this task: 47 STATE task tests PASS.
Cross-cutting transition/replay/invariant/security suites are additionally run at Batch 04 level.

## Acceptance boundary
PASS means implementation evidence only. It does not mean Section 15 accepted, runtime product accepted, real-book E2E accepted, or release authorized.
