# Queue Integration Plan

1. Orchestrator emits a `TaskMessage` only after stage readiness is established.
2. Message carries stable task_id + idempotency_key + attempt + artifact references.
3. Workers poll only queues/routing tags matching their capabilities.
4. On delivery, worker runtime still acquires lease before execution.
5. ACK only after lease-guarded state/artifact commit succeeds.
6. NACK on retryable transport/executor failure.
7. Visibility timeout handles worker disappearance.
8. Dead-letter entries create infrastructure evidence and remediation routing.
9. Backpressure feeds orchestration admission control.
10. Queue transport may be replaced without changing stage semantics.
