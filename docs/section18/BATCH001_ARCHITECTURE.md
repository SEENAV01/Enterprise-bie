# Section 18 Batch 001 architecture

Batch 001 implements the first 10 original Section 18 tasks:

1. BIE-APP-RUN-001 create run
2. BIE-APP-RUN-002 upload/import source
3. BIE-APP-RUN-003 source validation UI
4. BIE-APP-RUN-004 run status
5. BIE-APP-RUN-005 stage timeline
6. BIE-APP-RUN-006 failure view
7. BIE-APP-RUN-007 retry controls
8. BIE-APP-RUN-008 cancel/pause/resume
9. BIE-APP-GRAPH-001 concept graph viewer
10. BIE-APP-GRAPH-002 prerequisite graph viewer

## Architecture rule

The product/operator layer is a window into BIE, not a second engine. It reuses:

- `PdfInspectionJobService`
- `SQLitePersistence`
- `SQLiteDurableTaskQueue`
- `SQLiteIdempotencyStore`
- `FileSystemCAS`
- canonical Knowledge Intelligence graph validation/query
- canonical `PrerequisiteGraph`

The new `SQLiteOperatorStore` contains only product identity, attempt bindings and operator events. It intentionally does not copy source bytes or engine artifacts.

## Truthful lifecycle

A product run begins as DRAFT. Importing a bounded PDF delegates storage and queueing to the canonical job service and binds the resulting canonical job. READY/RUNNING/SUCCEEDED/FAILED status is read from canonical state. PAUSED/CANCELLED are real operator controls over an undelivered durable queue task. In-flight cancellation is unsupported in this batch and fails closed.

Retry preserves the failed canonical job/evidence and creates a new attempt-specific canonical job after reading the original source through CAS integrity verification.

## UI

Source validation, status, timeline, failure and graph renderers provide server-renderable accessible HTML. Graph views use deterministic SVG plus text fallbacks. The local development router is opt-in via `BIE_SECTION18_LOCAL_OPERATOR=1`; it makes no authentication or deployment claim.

## Acceptance boundary

This is Batch 001 implementation evidence, not Section 18 completion. It does not claim a full book-to-video/game user flow, authenticated multi-tenant operation, production deployment, or product acceptance.
