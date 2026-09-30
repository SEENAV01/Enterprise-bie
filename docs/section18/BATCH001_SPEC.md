# BIE Section 18 — Batch 001 specification

Baseline: `47cafba8975061555764c3c579ae6daad696ae64`, the verified Section 17 merge on `main`.

This batch implements the first ten original Section 18 registry capabilities:
`BIE-APP-RUN-001..008` and `BIE-APP-GRAPH-001..002`.

## Architecture

The app is an operator/product window over existing BIE stores. It deliberately
reuses `PdfInspectionJobService`, `SQLitePersistence`,
`SQLiteDurableTaskQueue`, `SQLiteIdempotencyStore` and `FileSystemCAS`.
The additive operator-control database stores only pause/resume/cancel intent and
control events; it is not a parallel run/artifact backend.

The first supported source profile is bounded PDF, matching the already-existing
API/Android path. Raw source bytes remain in the canonical CAS and are not
returned by Section 18 status/failure/graph endpoints.

## Observable behavior

- Validate a bounded PDF and show digest/size/issues without pretending validation
  means learning or product acceptance.
- Create a durable run with idempotent request identity.
- Read persisted run/queue/control status after service restart.
- Render the actual persisted stage timeline; no synthetic percent-complete field.
- Inspect safe diagnostic codes and evidence refs after a governed failure.
- Retry only a failed dead-lettered attempt; create a new attempt/task identity
  and retain earlier failure evidence.
- Pause/resume READY work and cooperatively cancel READY/RUNNING work. Cancellation
  blocks output publication and writes evidence.
- Render concept/prerequisite graphs only from an artifact that exists in the
  canonical persistence/CAS and belongs to the requested run.
- Serve a responsive, keyboard-focusable operator UI at `/app/` backed by the
  new `/v1/app` routes.

## Fail-closed rules

Wrong media type, oversize/empty/non-PDF source, idempotency conflicts, unknown
runs/artifacts, cross-run graph access, malformed graph JSON, dangling graph
edges, invalid control transitions and unsafe retry requests do not become a
successful-looking UI state.

## Evidence and tests

The batch runner executes all Section 18 tests plus the two inherited
productization API suites. A separate Playwright/Chromium smoke opens the real
served UI, uploads a real structural PDF fixture, validates/creates a persisted
run, exercises pause/resume/cancel, verifies mobile overflow and emits desktop
and mobile screenshots. CI packages evidence only after those checks pass.

## Acceptance boundary

This is an implementation candidate for ten original tasks, not Section 18
completion. Reasoning viewer, lesson/director/SceneIR/game-plan views, artifact
explorers, generated-code/render/game previews, QA dashboards and admin/operator
panels remain in later original tasks. Authentication/tenant isolation,
production deployment, full real-book BIE execution, video/game acceptance and
independent learner/product acceptance are not claimed here. Task 028 remains
paused.
