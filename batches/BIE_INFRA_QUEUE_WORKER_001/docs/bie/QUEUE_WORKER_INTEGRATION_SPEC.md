# BIE-INFRA-QUEUE-WORKER-001 — Queue-to-Worker Consumer Loop, ACK-after-Fenced-Commit & Retry Policy Integration

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Join the durable task queue to the worker executor runtime so task delivery, worker execution, lease/fencing, commit, ACK/NACK and dead-letter behavior operate as one end-to-end execution loop.

## Canonical lifecycle
1. Worker polls durable queue using its capability tags.
2. Queue marks message DELIVERED with visibility timeout.
3. Consumer resolves the stage resource requirement and executor.
4. Worker runtime selects/reserves worker capacity and acquires lease.
5. Executor runs and may heartbeat.
6. State/artifact/evidence commit is fenced by current ownership.
7. Only after successful fenced commit does consumer ACK the queue message.
8. Retryable failures NACK with delay/backoff.
9. Permanent failures or exhausted retries go to DEAD_LETTER.
10. Dead-letter creates infrastructure evidence/remediation routing.

## Invariants
1. Queue ACK is impossible before successful worker-runtime completion.
2. Fenced commit failure cannot be ACKed.
3. Executor failure cannot be ACKed.
4. Retry policy is explicit and deterministic.
5. Delivery attempt count and stage attempt number remain distinct.
6. Redelivery of the same queue message is safe because execution uses stage idempotency + lease fencing.
7. Retryable transport/runtime failures NACK.
8. Permanent contract/validation failures dead-letter immediately.
9. Max deliveries still enforced by the queue.
10. Consumer crashes before ACK yield visibility-timeout redelivery.
11. Worker capability tags filter polling but do not bypass scheduler hard requirements.
12. Queue/consumer layer never declares stage or release SUCCESS by itself.

## Retry policy
Reference policy distinguishes:
- RETRYABLE: transient worker/runtime/lease/resource/transport failure
- PERMANENT: invalid task contract, missing executor definition, unsupported stage contract
- SUCCESS: fenced commit completed

Optional deterministic linear/exponential backoff metadata is represented by policy.

## Production direction
Reference consumer is synchronous. Production can use long-running async consumers while preserving ACK-after-fenced-commit semantics.
