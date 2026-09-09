# Worker Executor Runtime Integration Plan

1. Orchestrator resolves stage requirements.
2. CapabilityScheduler selects worker.
3. Runtime reserves worker capacity.
4. LeaseManager acquires `(run, stage, attempt)` ownership.
5. Remote/local worker executor runs with heartbeat callback.
6. Every state/artifact/evidence commit is fenced.
7. Runtime releases lease + capacity in `finally`.
8. Worker capability snapshot, fencing token and execution metadata become evidence.
9. Long render/game/browser jobs heartbeat periodically.
10. Production async queue transport must preserve the same token and commit semantics.
