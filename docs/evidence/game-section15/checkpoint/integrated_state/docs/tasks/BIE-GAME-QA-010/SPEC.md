# BIE-GAME-QA-010 — legacy keyword/slide generator retirement and unsafe-dispatch scan

## Purpose
Implement the Section 15 GAME-internal QA capability **legacy keyword/slide generator retirement and unsafe-dispatch scan**. This is not Section 16 QA and cannot grant product acceptance.

## Capability-specific contract
Reject legacy keyword-based game generators, MCQ/slide-only generator entrypoints and unsafe eval/exec/compile routing. Non-blocking hardening observations remain visible.

## Enterprise invariants
- deterministic evidence for identical governed inputs;
- explicit PASS/FAIL findings rather than silent fallback;
- blocking findings are ERROR/CRITICAL and cannot be hidden by score aggregation;
- provenance/evidence references remain attached to findings/results;
- caller/source implementation is not mutated to obtain a green QA result;
- anti-slide/studio-quality intent remains enforced;
- runtime claims require real runtime evidence where applicable;
- thresholds are policy-driven and fail closed;
- `product_accepted=false`.

## Verification
Atomic task tests: 7. Cumulative QA checkpoint at this task: 70 tests. Batch 08 also includes 17 cross-cutting contract/pipeline/architecture tests and upstream regression gates.

## Evidence
`evidence/batch08/tasks/BIE-GAME-QA-010/TASK_RESULT.json` stores the canonical gate result, findings, metrics, QA receipt and cumulative checkpoint.

## Acceptance boundary
PASS means this GAME-internal implementation gate passed on the governed fixtures/runtime evidence. It does not mean Section 15 implementation-scope complete, real-book E2E accepted, Section 16 QA accepted, or product accepted.
