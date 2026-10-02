# H1-005: local CAS capacity and interrupted dispatch

This is finding-derived Section18 hardening, not a new original task and not
Section18 sign-off. Canonical persistence, queue, idempotency and CAS contracts
remain unchanged. Task028 remains paused; product acceptance and deployment
remain false.

## Reproduced findings and minimal changes

- Aggregate physical CAS capacity was unbounded. A lower-only persisted budget
  and bounded physical inventory now guard canonical CAS writes under one
  root-wide OS lock. Interrupted `.cas-*` data counts against capacity and is
  retained. No automatic evidence deletion or distributed storage claim.
- A dispatch process could die with unused catalogue audit credits. Authorized
  reconciliation requires an exact persisted record hash and idempotency key.
  It fences dispatch admission and settles only unused credits; it does not
  terminate a process or fabricate a native job transition. RUNNING delivery
  requires review, not heartbeat-based death inference.
- A real completion/reconciliation scheduling cut consumed credits before a
  late finish. Late finish accepts only a verified, durable STOPPED/reconciled
  record. Missing credits without that record still fail closed.
- Real SQLite last-close removed WAL between catalogue file checks. A single
  no-follow stat now tolerates absent startup/volatile files, rejects nonregular
  files and hardlinks, and retains the exact database/WAL byte ceilings.
- Genuine CAS exhaustion during a canonical inspection can also exhaust the
  failure artifact write. The adapter performs only verified RUNNING/DELIVERED
  failure/dead-letter transitions, with no invented evidence artifact.

## Evidence and scope

Focused local collection: 59 distinct methods, zero failures/errors/skips:
CAS22, worker17, catalogue7, Section17 maintenance13. The latter is separately
owned by H1-006; it is not counted twice or as an original Section18 task.
The earlier cumulative650 run passed before the catalogue and LF-pin repairs;
the expanded cumulative658 candidate also passed locally with zero
failures/errors/skips. Hosted/native and full canonical gates remain open.

Controls include real competing processes, actual terminated lock owners,
actual process crashes, restart/replay, exact-capacity admission, byte-over
rejection, revoked/foreign principals, hardlink rejection and tamper controls.
Failed pre-repair evidence and exact before-images are retained outside Git in
the authoritative Section18 deliverables workspace.

The browser recovery action is an explicit authorized admission fence. It does
not label the native job cancelled, kill a worker, retry automatically, infer
death, or imply distributed transaction atomicity. Full quota/recovery audit,
native render, coherent full-flow, re-audit, final master and complete canonical
regression are still required before any integration PR.
