# Recovery Integration Plan

1. Before `RUNNING`, orchestrator acquires lease for `(run_id, stage_id, attempt)`.
2. Worker heartbeats renew the lease during long tasks.
3. Every worker-originated state/artifact/evidence write carries worker_id + fencing_token.
4. Persistence and artifact stores call `WorkerOwnershipGuard` before commit.
5. On worker crash, lease expires; recovery scanner emits recovery evidence and marks stage attempt FAILED/recoverable according to run-state policy.
6. New worker acquires same attempt only if recovery policy allows, otherwise orchestrator creates a retry attempt.
7. Old worker writes after takeover are rejected by fencing token.
8. Render workers and game-runtime workers use the same ownership contract.
9. Distributed backend should use atomic database/coordination primitives, not process-local locks.
