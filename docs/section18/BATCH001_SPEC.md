# BIE Section 18 — Batch 001

Canonical base: `47cafba8975061555764c3c579ae6daad696ae64`

This batch implements the first ten original Section 18 entries:

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

## Architecture

The implementation is an operator/product layer over canonical BIE components. It
does not fork the engine. Raw PDF bytes remain in the canonical CAS; persisted run
state remains in SQLitePersistence; work remains in SQLiteDurableTaskQueue. The
Section 18 sidecar stores only display metadata and operator intent/audit events.

Create/import/status/timeline/failure/retry flows execute against the actual
`PdfInspectionJobService`. Pause/cancel for an unclaimed READY task uses the
canonical queue's dead-letter/redrive primitives. Once a worker has claimed a task,
pause/cancel fails closed rather than pretending preemption exists.

Concept and prerequisite viewers consume the current canonical knowledge/prerequisite
graph shapes. They validate bounds, reject malformed/cyclic/inconsistent graphs, and
render deterministic escaped semantic HTML.

## Acceptance boundary

This is Batch 001, not Section 18 completion. It does not claim:
- a complete web/mobile product;
- authentication or tenant isolation;
- running-task preemption;
- Section 18's remaining 23 original tasks;
- real-book video/game product acceptance;
- production deployment.

Those remain later Section 18 work and downstream acceptance.
