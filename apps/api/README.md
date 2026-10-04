# BIE API

This directory contains the local HTTP boundary for My Book Intelligence Engine.
Canonical engines remain under `bie/`; both inspection modes delegate to
`bie.document_intelligence.real_pdf_toc_runtime.inspect_real_pdf_toc`.

## Endpoints

- `GET /healthz` reports HTTP process liveness only.
- `GET /v1/capabilities` reports the service's current bounded capabilities.
- `POST /v1/documents/inspect` accepts a raw `application/pdf` request body and
  returns the Task 016 safe deterministic representation.
- `POST /v1/jobs/document-inspection` accepts the same bounded raw PDF body plus
  an `Idempotency-Key` header and returns HTTP 202 with a durable job ID.
- `GET /v1/jobs/{job_id}` returns safe persisted job and queue status.
- `GET /v1/jobs/{job_id}/result` returns the exact safe Task 016 result after
  success; pending or failed jobs return HTTP 409.

The inspection endpoint accepts at most 25 MiB and fails closed for unsupported
media types, empty bodies, oversized requests, and PDFs the governed runtime cannot
inspect. It does not accept multipart form data and never returns raw book text,
heading text, outline titles, PDF bytes, or local paths. The asynchronous
submission uses 400 for a missing or invalid key and 409 if a previously used
key is submitted with different PDF bytes. After trimming, keys must contain
1–128 ASCII letters, digits, periods, underscores, colons, or hyphens.

## Run locally

From the repository root after installing the API and Document Intelligence extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[document-intelligence,document-intelligence-layout,api]"
.\.venv\Scripts\python.exe scripts\run_bie_local_stack.py
```

This one command supervises the existing API runner and a separate continuous
PDF worker. The default is `127.0.0.1:8000`. Only literal loopback addresses are
allowed by this stack; `0.0.0.0` and other public binds are rejected. Use `--port`
to select another port. Health readiness is bounded to 20 seconds by default.
If either child unexpectedly exits, the stack stops its other child and exits
non-zero. Child logs are suppressed; stack output contains only safe lifecycle
events, never private storage paths or document/parser content.

The API and worker share exactly one resolved `BIE_DATA_ROOT`, defaulting to
the existing `~/.bie/api` policy. Set it in the process environment to a private
API data directory before launching. Runs, queue items and idempotency claims
remain in canonical SQLite stores; source PDF bytes, safe results and safe
execution evidence remain in canonical local CAS. Keep that directory private.
No source PDF download endpoint is provided.

To run the API and worker separately, or retain the existing one-job behavior:

```powershell
.\.venv\Scripts\python.exe scripts\run_bie_api.py
.\.venv\Scripts\python.exe scripts\run_bie_pdf_worker.py --once
.\.venv\Scripts\python.exe scripts\run_bie_pdf_worker.py --serve --poll-interval 1.0
```

No mode still means one job; `--once` and `--serve` are mutually exclusive.
The continuous worker calls `PdfInspectionJobService.run_once` sequentially.
`IDLE` waits 1 second by default, configurable from 0.1 to 60 seconds. A governed
`FAILED` document is counted and the worker continues. An unexpected service/
store failure stops the process safely; there is no automatic retry/redrive.
Only in-process `jobs_acked`, `jobs_failed`, and `idle_polls` counters are reported.

Ctrl+C/SIGINT and SIGTERM request cooperative stop: no next job is fetched and
the current job can finish. The stack's default graceful shutdown allowance is
20 seconds, followed by bounded terminate/kill cleanup. If a running job exceeds
that allowance, its persisted state must be inspected; forced process shutdown
does not mark the job cancelled or successful. `--shutdown-grace` and
`--readiness-timeout` accept 0.1–120 seconds. This is a development supervisor,
not a production process manager or distributed recovery system.

For owned automation, `BIE_LOCAL_STACK_CONTROL_STDIN=1` makes closing the stack's
stdin request the same shutdown. The stack uses a private stdin pipe to request
worker stop on consoleless Windows as well. These are local process controls,
not HTTP endpoints. Leave these variables unset for ordinary interactive use.

## Section18 namespace boundary

**Task028's worker and stack are only for `apps/api` `/v1/jobs` state. Never use
a Section18 operator data root or any of its per-run directories.** Known
`operator.sqlite3` roots and descendants are rejected before stores open and
before continuous polls. This guard prevents accidental crossover; it is not a
security boundary against an OS administrator relocating or rewriting stores.

The stack launches only `run_bie_api.py` and `run_bie_pdf_worker.py --serve`.
Section18's `run_bie_operator.py`, `run_bie_operator_worker.py`, permissions,
tenant/admission/control/preview paths remain separate. No render, game, QA or
EVAL worker is launched here. Existing `/v1/capabilities` remains unchanged:
`local_manual_run_once_v1` still identifies its original worker contract; this
launcher adds local orchestration without revising that API schema.

## Current boundary

This is a local development service. Its SQLite/CAS persistence is local only.
It has no authentication, authorization, tenant isolation, encryption-at-rest
claim, rate limiting, wildcard CORS, distributed transaction guarantee, or
public deployment hardening. A successful health response or PDF inspection
does not prove product acceptance, real-book end-to-end acceptance, Android
physical-device acceptance, or downstream media/game acceptance.

Tasks 1–27/27A and Sections 1–18 are preserved. Task028 resumes the original
productization program from Section18's merged canonical state. Continuous PDF
inspection does not implement the autonomous all-intelligence book-to-video/game
producer; those productization and final acceptance obligations remain open.
