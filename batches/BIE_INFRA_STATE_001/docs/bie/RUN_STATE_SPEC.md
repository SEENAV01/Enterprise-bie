# BIE-INFRA-STATE-001 — Enterprise Run State Machine & Typed Stage Transition Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Make BIE's canonical enterprise execution graph operationally safe.

A run is no longer a sequence of loosely related function calls. Each stage has an explicit lifecycle, prerequisites, attempts, input/output artifact references, failure evidence, retry semantics and repair lineage.

## Stage lifecycle
PENDING → READY → RUNNING → SUCCEEDED
                    ↘ FAILED → READY (retry)
                    ↘ BLOCKED
SUCCEEDED → INVALIDATED → READY

Terminal release state is computed elsewhere by evidence-backed ReleaseEvaluator; stage success never means product release success.

## Core invariants
1. A stage can become READY only when all required predecessor stages SUCCEEDED.
2. RUNNING requires READY.
3. SUCCEEDED requires output artifact refs.
4. FAILED requires diagnostic evidence and remediation owner.
5. Retry increments attempt number and preserves previous attempt history.
6. Repair creates a new attempt; it never rewrites old failed evidence.
7. If an upstream artifact changes, dependent succeeded stages can be INVALIDATED.
8. Resume starts only from valid READY/PENDING states; completed valid stages need not rerun.
9. No stage can mark RELEASE_MANIFEST successful by itself.
10. Run state is independent of model/provider.
11. Every transition is timestamped and auditable.
12. Illegal transitions fail closed.

## Run lifecycle
CREATED → ACTIVE → BLOCKED / ACTIVE → EXECUTION_COMPLETE
EXECUTION_COMPLETE does NOT mean RELEASED.
Release is determined by the separate QA Release contract.

## Crash/resume
Persisted state contains all stage attempts and artifact refs. A process crash while RUNNING is recovered to FAILED/READY according to recovery policy; it is never silently treated as success.
