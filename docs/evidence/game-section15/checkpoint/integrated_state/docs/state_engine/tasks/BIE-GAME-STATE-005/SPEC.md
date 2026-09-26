# BIE-GAME-STATE-005 — challenge state

## Status
Original enterprise-depth implementation for Section 15 Batch 04. Individually traceable inside the cumulative batch.

## Purpose
Explicit READY/ACTIVE/SUCCEEDED/FAILED lifecycle with attempts, hint usage and history fingerprints.

## Inputs
- Batch-01 typed Game IR / StateModel / InteractionContract / safe Expr AST.
- Immutable or caller-owned state values; task code must not mutate upstream objects.
- Provenance-grounded rules/actions already validated by the DSL layer.

## Output contract
Handler: `challenge lifecycle transitions` in `bie/game_engine/state_engine/challenge_state.py`.
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
- start locked challenge
- attempt terminal challenge
- hint outside active state
- finish invalid state

## Verification
Atomic suite: `tests/state_engine/test_state_005_challenge_state.py` — 12 tests.
Cumulative checkpoint after this task: 59 STATE task tests PASS.
Cross-cutting transition/replay/invariant/security suites are additionally run at Batch 04 level.

## Acceptance boundary
PASS means implementation evidence only. It does not mean Section 15 accepted, runtime product accepted, real-book E2E accepted, or release authorized.
