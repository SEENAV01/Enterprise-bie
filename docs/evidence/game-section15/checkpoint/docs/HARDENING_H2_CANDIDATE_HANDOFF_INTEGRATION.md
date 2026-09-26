# Section 15 GAME Hardening H2 — Candidate QA / Director Materialization / Canonical Handoffs

Closes GAME-AUD-004, GAME-AUD-005 and GAME-AUD-006 from Step-2 audit.

## Candidate-driven QA
Production `run_game_qa()` requires a validated `CandidateGameEvidence`; it does not import or construct synthetic fixtures. Candidate evidence cross-binds Strategy signals, Director plans, GameDocument, CompilerContext, CompiledBundle, RuntimeBuildResult, state transition system, multi-domain benchmark records and source-root scan evidence. Tampered compile/runtime/objective bindings fail closed.

## Director materializer
`DirectorPlan` plus explicit objective text/visual/provenance inputs deterministically produces an executable typed `GameDocument`, text catalog, scoring/mastery policies and runtime capability requirements. Missing text/visual coverage is rejected rather than guessed. The resulting candidate is successfully compiled, built in real runtime and passed through all 10 GAME-QA gates.

## Canonical upstream adapters
The adapter is pinned to current canonical blob identities for `bie/director/game_handoff.py`, `bie/reasoning/game_decision.py` and `bie/pedagogy/pedagogy_plan_contract.py`. It preserves evidence IDs, rejects unresolved/review/low-confidence pedagogy decisions, rejects unsupported strategy signals (for example MAP without coordinates), and produces validated Strategy/Director inputs.

## Boundary
H2 does not close sandbox/canonical browser-worker integration, deployed native ESM origin, audio runtime, full accessibility/localization, rights, performance, durability, telemetry persistence, mastery persistence, DSL packaging traceability, canonical legacy migration or fuzz/property testing. Product acceptance remains false.
