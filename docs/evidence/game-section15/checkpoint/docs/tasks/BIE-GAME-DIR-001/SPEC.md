# BIE-GAME-DIR-001 — game experience planner

## Purpose
Implement the governed game experience planner capability as an independent Director component.

## Enterprise invariants
- structured StrategyDecision only; no raw-keyword routing
- source/reasoning/objective provenance preserved
- deterministic stable output
- fail closed on unsupported runtime/ambiguous strategy/invalid mastery data
- anti-slide default and active learning preserved
- accessibility requirements propagated
- no premature answer reveal
- no speed-pressure scoring
- product acceptance remains false

## Verification
Capability-specific positive, negative, determinism, provenance and studio-quality tests plus cumulative dependency regression.
