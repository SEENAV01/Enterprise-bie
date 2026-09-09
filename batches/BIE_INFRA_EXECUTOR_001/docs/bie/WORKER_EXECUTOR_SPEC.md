# BIE-INFRA-EXECUTOR-001 — Worker Executor Runtime, Heartbeat & Lease-Guarded Commit Adapter

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Join capability-aware scheduling, worker leases, execution, heartbeats, fenced commits and cleanup into one safe worker-runtime contract.

## Canonical lifecycle
1. Scheduler selects eligible worker.
2. Scheduler reserves capacity.
3. Lease is acquired for `(run_id, stage_id, attempt)`.
4. Executor starts with worker identity + fencing token.
5. Heartbeats renew lease during long execution.
6. Worker produces outputs/evidence.
7. Before commit, ownership guard validates worker + fencing token + lease freshness.
8. Artifact/state commit occurs.
9. Lease and scheduler capacity are released.
10. Failure follows the same cleanup path and emits structured evidence.

## Invariants
1. No worker execution starts without capacity reservation and lease.
2. No worker-originated commit is accepted without a current fencing token.
3. Heartbeats may extend lease but cannot change worker ownership.
4. Expired lease blocks commit.
5. Cleanup is attempted on success and failure.
6. Capacity must not leak after normal completion.
7. A stale worker cannot commit after takeover.
8. Duplicate completion does not create duplicate ownership.
9. Worker runtime does not decide release SUCCESS.
10. Domain intelligence remains inside stage executors, not runtime plumbing.
11. Provider-specific model logic remains outside this runtime.
12. Runtime diagnostics are structured and evidence-backed.

## Failure handling
- scheduling failure → task not started
- lease acquisition failure → release reserved capacity
- execution failure → structured failure evidence
- heartbeat failure → execution becomes non-committable
- commit guard failure → outputs rejected
- cleanup failure → emitted as infrastructure diagnostic

## Future production direction
The reference runtime is synchronous and deterministic for testing. Production may use async workers, queues and remote executors while preserving the same ownership and commit semantics.
