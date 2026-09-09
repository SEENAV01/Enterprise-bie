# Persistence Integration Plan

1. Persist RunStateMachine after every state transition.
2. Persist executor outputs and evidence catalog records in the same orchestration transaction boundary where practical.
3. Keep artifact bytes in CAS/object storage; persist only metadata, hashes and lineage in SQL.
4. On restart, reconstruct run state from SQL, then verify referenced blobs against CAS.
5. Recover stale RUNNING attempts explicitly; never auto-promote them to SUCCEEDED.
6. Move reference SQLite backend to PostgreSQL for distributed workers.
7. Add migrations before schema version changes.
8. Add optimistic/row-level locking for multi-worker execution.
9. Add retention and archival policies only after release lineage requirements are finalized.
