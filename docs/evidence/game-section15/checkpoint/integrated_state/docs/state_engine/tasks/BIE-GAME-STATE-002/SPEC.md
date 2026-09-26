# BIE-GAME-STATE-002 — manipulables

## Status
Original enterprise-depth implementation for Section 15 Batch 04. Individually traceable inside the cumulative batch.

## Purpose
Compile accessible Game IR actions into deterministic command bindings with typed action payload validation.

## Inputs
- Batch-01 typed Game IR / StateModel / InteractionContract / safe Expr AST.
- Immutable or caller-owned state values; task code must not mutate upstream objects.
- Provenance-grounded rules/actions already validated by the DSL layer.

## Output contract
Handler: `compile_actions / normalize_command` in `bie/game_engine/state_engine/manipulables.py`.
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
- missing visual target
- missing drag coordinates
- bad coordinate type
- unknown action
- duplicate payload key

## Verification
Atomic suite: `tests/state_engine/test_state_002_manipulables.py` — 11 tests.
Cumulative checkpoint after this task: 23 STATE task tests PASS.
Cross-cutting transition/replay/invariant/security suites are additionally run at Batch 04 level.

## Acceptance boundary
PASS means implementation evidence only. It does not mean Section 15 accepted, runtime product accepted, real-book E2E accepted, or release authorized.
