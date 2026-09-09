# BIE-INFRA-ORCH-001 — Enterprise Orchestrator Skeleton & Stage Executor Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Turn the enterprise execution graph and run-state rules into an executable orchestration layer.

The orchestrator owns dependency-aware scheduling, typed artifact handoff, executor invocation, failure routing, retry/resume, idempotency and audit-safe execution. It does not contain domain intelligence.

## Invariants
1. Control flow is separated from educational intelligence.
2. Every executable stage has a registered executor.
3. Stages receive only declared upstream artifacts and execution context.
4. Success requires output artifacts and evidence.
5. Exceptions fail closed into structured FAILED attempts.
6. Downstream scheduling stops after failure until explicit retry/repair.
7. Completed valid stages are reusable on resume.
8. Executors receive deterministic idempotency keys.
9. The orchestrator cannot itself declare product release SUCCESS.
10. RELEASE_MANIFEST remains downstream of RELEASE_EVALUATION.
11. Scheduling is deterministic for identical graph and state.
12. Provider-specific model/tool logic stays outside orchestration.

## Executor contract
Input: run id, stage id, attempt, idempotency key, input artifact refs, configuration and metadata.
Output: output artifact refs, evidence refs, diagnostics and metadata.
Failure: diagnostics, evidence refs and remediation owner.

## Resume semantics
SUCCEEDED stages are preserved. FAILED stages require explicit retry. PENDING stages become READY only after predecessor success. Persisted RUNNING stages after a crash require recovery; they are never assumed successful.
