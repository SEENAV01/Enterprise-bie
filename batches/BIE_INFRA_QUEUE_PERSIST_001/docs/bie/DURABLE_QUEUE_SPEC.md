# BIE-INFRA-QUEUE-PERSIST-001 — Durable SQL Queue Persistence, Visibility Recovery & Dead-Letter Storage

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Persist BIE task-queue state durably so queued, delivered, retried and dead-lettered work survives process restarts.

The reference implementation uses SQLite and preserves the queue semantics defined by `BIE-INFRA-QUEUE-001`.

## Delivery semantics
- at-least-once delivery
- explicit ACK / NACK
- visibility timeout redelivery
- monotonic delivery count
- max-deliveries → dead-letter
- manual redrive
- stable task identity and idempotency key
- capability-tag routing
- priority ordering
- durable audit events

## Core invariants
1. READY messages survive process restart.
2. DELIVERED messages survive process restart.
3. Expired DELIVERED messages are recovered to READY or DEAD_LETTER.
4. ACKED messages are never redelivered.
5. DEAD_LETTER messages remain durable until redrive/retention policy.
6. Duplicate enqueue with same semantic identity is idempotent.
7. Conflicting reuse of task_id is rejected.
8. Delivery count is monotonic and durable.
9. Consumer ownership is checked on ACK/NACK.
10. Queue mutations are transactional.
11. Backpressure counts durable READY and DELIVERED records.
12. Queue payloads reference artifacts; large payload blobs stay outside SQL queue rows.
13. Queue transport cannot mark stage/release success.
14. Schema version is explicit and migration-safe.

## Reference tables
- schema_meta
- queue_tasks
- queue_events

`queue_tasks` stores current task/delivery state.
`queue_events` stores immutable queue lifecycle evidence.

## Restart recovery
On startup/poll:
- scan DELIVERED rows whose `visible_at <= now`
- if delivery_count < max_deliveries → READY
- otherwise → DEAD_LETTER
- append immutable recovery event

## Production direction
SQLite is the contract reference backend. A distributed implementation can later use PostgreSQL, Redis Streams, SQS or another queue system while preserving these semantics.
