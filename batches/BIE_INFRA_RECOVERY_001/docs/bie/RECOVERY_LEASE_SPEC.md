# BIE-INFRA-RECOVERY-001 — Crash Recovery, Lease & Worker Ownership Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Provide distributed-safe stage ownership so BIE workers can execute long-running textbook, render and game tasks without duplicate ownership, silent abandonment or unsafe takeover.

## Core concepts
- Worker: execution agent with stable worker_id.
- Lease: time-bounded ownership claim over one `(run_id, stage_id, attempt)`.
- Heartbeat: lease renewal proving worker liveness.
- Fencing token: monotonically increasing ownership generation. Any write from an older token is rejected.
- Recovery: expired lease is explicitly marked stale, then a new worker may acquire ownership using a higher fencing token.

## Invariants
1. At most one active lease may own a stage attempt.
2. Lease ownership is scoped to run, stage and attempt.
3. A worker cannot complete/write a stage using an expired lease.
4. Renewals require matching worker and fencing token.
5. Takeover after expiry increments fencing token.
6. Old/stale workers are fenced from future state/artifact commits.
7. Crash recovery never promotes a stage to SUCCEEDED.
8. Lease expiry creates recovery evidence.
9. Retry attempts receive new ownership; attempt numbers remain immutable.
10. Worker ownership contains no provider-specific AI logic.
11. Clock decisions use one authoritative lease-store clock in production.
12. Release success remains independent of worker lease state.

## Lease lifecycle
AVAILABLE → LEASED → RENEWED* → RELEASED
                      ↘ EXPIRED → RECOVERABLE → LEASED(new fencing token)

## Commit guard
Any stage-state mutation or artifact registration caused by a worker must carry:
- run_id
- stage_id
- attempt
- worker_id
- fencing_token

The persistence/artifact layer verifies this tuple before accepting worker-owned writes.

## Production implementation direction
Reference implementation in this task is an in-memory lease manager using an injectable clock. Distributed production should store leases transactionally in PostgreSQL/Redis-compatible coordination infrastructure with atomic compare-and-swap semantics and a server-side clock.
