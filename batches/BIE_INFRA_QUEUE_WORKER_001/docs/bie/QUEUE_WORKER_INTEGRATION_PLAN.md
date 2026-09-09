# Queue-to-Worker Integration Plan

1. Durable queue becomes the orchestrator-to-worker transport.
2. Consumer polls by advertised worker capability tags.
3. Stage requirement registry and executor registry resolve by stage_id.
4. Worker runtime still performs hard scheduling + lease acquisition.
5. Executor runs with heartbeat-capable context.
6. Commit adapter persists ArtifactEnvelope, evidence and state transition under fencing guard.
7. Queue ACK occurs only after commit returns successfully.
8. Runtime/commit failures NACK using deterministic retry policy.
9. Missing contracts/executors are permanent failures and dead-letter immediately.
10. Dead-letter messages generate INFRA evidence and remediation tasks.
11. Production async consumers preserve identical ACK timing.
