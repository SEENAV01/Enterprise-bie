# BIE-GAME-STATE-007 — failure conditions

## Status
Original enterprise-depth implementation for Section 15 Batch 04. Individually traceable inside the cumulative batch.

## Purpose
Evaluate one-or-more failure predicates with matched-condition evidence and no silent success override.

## Inputs
- Batch-01 typed Game IR / StateModel / InteractionContract / safe Expr AST.
- Immutable or caller-owned state values; task code must not mutate upstream objects.
- Provenance-grounded rules/actions already validated by the DSL layer.

## Output contract
Handler: `evaluate_failure / evaluate_conditions` in `bie/game_engine/state_engine/conditions.py`.
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
- non-boolean condition
- success/failure conflict
- missing state value

## Verification
Atomic suite: `tests/state_engine/test_state_007_failure_conditions.py` — 6 tests.
Cumulative checkpoint after this task: 71 STATE task tests PASS.
Cross-cutting transition/replay/invariant/security suites are additionally run at Batch 04 level.

## Acceptance boundary
PASS means implementation evidence only. It does not mean Section 15 accepted, runtime product accepted, real-book E2E accepted, or release authorized.
