# BIE-INFRA-QUEUE-001 — Durable Task Queue, Delivery Semantics & Backpressure Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Define reliable task delivery between the BIE orchestrator and distributed workers.

The queue provides transport semantics only. Stage correctness, leases, fencing, artifact commits and release decisions remain owned by their existing contracts.

## Core delivery model
Reference semantics: **at-least-once delivery**.

A queue message may be delivered more than once. Duplicate safety is achieved by:
- stable task identity
- idempotency key
- stage attempt identity
- worker lease + fencing token
- artifact immutability

## Message lifecycle
READY → DELIVERED → ACKED
          ↘ NACKED → READY
          ↘ VISIBILITY_TIMEOUT → READY
          ↘ MAX_DELIVERIES → DEAD_LETTER

## Invariants
1. Every queued task has a stable task_id.
2. A message is never silently lost after delivery.
3. ACK removes the message from normal delivery.
4. NACK returns the message according to retry policy.
5. Visibility timeout requeues unacknowledged deliveries.
6. Delivery count is monotonic.
7. Exceeding max deliveries sends message to dead-letter state.
8. Queue may redeliver; consumers must be idempotent.
9. Priority affects ordering but does not bypass stage dependency rules.
10. Backpressure prevents unbounded in-flight work.
11. Per-capability queues or routing keys may be used.
12. Queue transport never marks stage success.
13. Queue transport never declares release success.
14. Payloads reference artifacts; large binary payloads do not belong in queue messages.
15. Queue state changes are auditable.

## Backpressure
Reference contract supports:
- max queued messages
- max in-flight deliveries
- per-consumer in-flight limits
- explicit enqueue rejection when capacity is exceeded.

## Production direction
The interface can later map to PostgreSQL-backed queues, Redis Streams, SQS, RabbitMQ, Kafka-style work queues, or Kubernetes-native execution while preserving delivery semantics.
