# Durable Queue Integration Plan

1. Replace the in-memory queue adapter with `SQLiteDurableTaskQueue` for local/reference execution.
2. Orchestrator enqueues only after stage readiness.
3. Worker ACK occurs only after lease-guarded artifact/state commit succeeds.
4. Visibility recovery runs on poll and can also run from a dedicated recovery worker.
5. Dead-letter events become infrastructure evidence artifacts.
6. Queue metrics feed admission control and worker autoscaling later.
7. For distributed production, move queue state to PostgreSQL or managed queue infrastructure.
8. Preserve stable task_id/idempotency_key across transport migrations.
9. Queue payloads continue to carry artifact references, not binary source/render payloads.
