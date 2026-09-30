# Section 18 APP — Batch 001

Canonical baseline: `47cafba8975061555764c3c579ae6daad696ae64`, the verified Section 17 merge on main.

Original tasks in this batch:
- BIE-APP-RUN-001 create run
- BIE-APP-RUN-002 upload/import source
- BIE-APP-RUN-003 source validation UI
- BIE-APP-RUN-004 run status
- BIE-APP-RUN-005 stage timeline
- BIE-APP-RUN-006 failure view
- BIE-APP-RUN-007 retry controls
- BIE-APP-RUN-008 cancel/pause/resume
- BIE-APP-GRAPH-001 concept graph viewer
- BIE-APP-GRAPH-002 prerequisite graph viewer

The implementation uses the canonical `SQLitePersistence` and `FileSystemCAS`. The additional operator-control database stores control intent/audit only and never replaces canonical run state. Pause/resume/cancel remain REQUESTED until an actual worker adapter acknowledges effect. Retry creates a new canonical READY attempt and reports `dispatch_required=true`; it does not pretend that queue dispatch happened.

The only run-creation profile in this first batch is `pdf_inspection_v1`, matching the repository's existing bounded productization path. Full BIE book→video/game run dispatch, authentication/tenant boundaries, production deployment, real browser/native Android execution and product acceptance remain later Section 18 work. Task 028 stays paused.
