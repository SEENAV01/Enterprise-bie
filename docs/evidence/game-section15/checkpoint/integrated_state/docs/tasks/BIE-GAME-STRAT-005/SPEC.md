# BIE-GAME-STRAT-005 — Prediction strategy

## Purpose
Commit-before-observe learning loop with explicit outcome metric and visual prediction-vs-observation comparison.

## Dependency
Batch 01 `BIE-GAME-DSL-001` studio-enterprise contracts are the typed/provenance foundation. Batch 01 files are preserved as the dependency baseline.

## Enterprise invariants
- capability-specific structured eligibility; no raw keyword routing;
- deterministic scoring and stable ranking;
- explicit objective coverage and evidence trace;
- runtime capability gating;
- studio-design requirements flow downstream to Director/Compiler;
- no slide-deck fallback as an implicit strategy;
- ambiguity/no-evidence causes abstention or fail-closed behavior;
- product acceptance remains false.

## Implementation
`bie/game_engine/strategy_engine/prediction.py`

## Verification
Positive eligibility, negative/blocked eligibility, runtime-capability failure, provenance/evidence, studio-quality requirement, deterministic repeatability, and acceptance-boundary tests are required.

## Acceptance boundary
Passing this task is implementation evidence only. It is not Section 15 acceptance and not product acceptance.
