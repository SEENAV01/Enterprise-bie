# BIE-INFRA-PERSIST-001 — Durable Run State & Artifact Catalog Persistence Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Make BIE crash-safe and resumable by persisting run state, stage attempts, transition events, artifact catalog metadata and lineage indexes durably.

This task defines a persistence boundary and includes a SQLite reference backend suitable for local development and tests. Enterprise production backends can later use PostgreSQL for metadata while artifact bytes remain in object storage/CAS.

## Invariants
1. Persisted run state is authoritative after process restart.
2. Stage attempts are append-preserving; failed evidence/history is never overwritten.
3. Transition events are durable and ordered.
4. Artifact catalog records are immutable by artifact_id.
5. Parent lineage is durable.
6. Writes are transactional.
7. Concurrent writers must not corrupt state.
8. A partially committed stage transition must not appear successful.
9. Persisted RUNNING stage recovered after crash is not treated as SUCCEEDED.
10. Schema version is explicit and migratable.
11. Unknown schema versions fail closed.
12. Artifact bytes and metadata storage remain separable.
13. Persistence layer contains no provider-specific AI logic.
14. Release status remains computed by ReleaseEvaluator, not inferred from persistence.

## Reference schema
Tables:
- schema_meta
- runs
- stages
- attempts
- transition_events
- artifact_records
- artifact_parents

## Resume contract
On startup:
- load run metadata
- reconstruct latest stage attempt state
- preserve prior attempts/events
- verify artifact references separately against CAS
- recover stale RUNNING attempts via explicit recovery policy
- continue orchestration only after consistency validation

## Production direction
SQLite is a reference implementation, not the final distributed metadata store. The interface should map cleanly to PostgreSQL with transactional writes, row-level locking, migrations and audit retention.
