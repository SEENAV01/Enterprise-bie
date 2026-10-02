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
- Real worker termination before ACK, or after ACK before idempotency completion,
  leaves a persisted successful attempt but interrupted bookkeeping. An explicit
  authorized action may finalize only that already-produced, hash-verified
  source/result/evidence and own queue/claim identity. It never re-extracts the
  PDF or rewrites the attempt/result. A second actual process cut during this
  recovery is safely replayable; one audit settlement is retained.
- A partial native run previously prevented the operator login flow from
  reaching recovery controls. `/operator/v1/workspace` now authenticates and
  verifies the catalogue independently of run health. It explicitly says
  `run_health_checked:false`; a partial run remains REVIEW_REQUIRED, not success.

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

## Current terminal recovery qualification (not final sign-off)

Twelve additional distinct terminal/workspace methods passed locally, including
real worker/reconciliation process termination, CAS corruption, foreign claim
owner, unauthorized/revoked access and catalogue tampering. The actual browser
desktop and phone recovery journeys passed two distinct methods over TCP. A
failed Windows sandbox Node EPERM attempt remains retained as environment
evidence, not a product failure or a passing assertion.

These12 methods extend H1-005 from46 to58; H1-006's13 controls remain separately
owned. The focused collection is71, and cumulative atomic identity is670.
Actual counts are promoted only from their executed receipts. Native render,
failed-terminal partial-transition disposition, full producer binding/full-flow,
complete audit/re-audit and full canonical regression are still open.

## Failed-terminal recovery controls

A genuine native-text PDF with an empty native outline title passes base source
inventory but fails canonical TOC inspection. Two actual worker process cuts
reproduced stranded FAILED/DELIVERED bookkeeping (three selected controls:
one PASS, two FAIL before repair). The minimal adapter correction verifies the
original failure transition, source identity, exact failure evidence, own
delivery and own CLAIMED idempotency record before finishing BLOCKED/dead-letter
bookkeeping. It creates no result/evidence, changes no attempt, does not rerun
inspection, and leaves the failed claim without a completed result.

All three controls passed after repair, including corrupted evidence refusal.
The fresh focused collection is74 distinct methods: H1-00561 and H1-00613;
zero failures/errors/skips. The cumulative expected identity becomes673 but
must not be claimed passed until its fresh receipt exists. The previous670
receipt predates these three methods and a strengthened restart-route check.

The retained full Windows browser run has23 methods,21 PASS and two teardown
ERRORs. A stage-only diagnostic rerun proved UI assertions reached completion
before duplicate JS/Windows forced-cleanup ownership failed. The correction
uses only the established private Job Object owner, still requires zero active
processes and confined profile cleanup, and does not change Linux cleanup or
product/security assertions. Fresh whole-browser qualification is still required.
