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
.\.venv\Scripts\python.exe scripts\run_bie_api.py
```

The default bind is `127.0.0.1:8000`, with reload and debug behavior disabled.
To process one queued job in a separate process, run:

```powershell
.\.venv\Scripts\python.exe scripts\run_bie_pdf_worker.py --once
```

The API and worker use `BIE_DATA_ROOT`, defaulting to the user's
`~/.bie/api` directory. They store runs, queue items, and idempotency claims
in local SQLite files and store raw source PDF bytes, safe results, and safe
execution evidence in a local content-addressed store. Keep this directory
private. Task 020 makes no encryption-at-rest claim. No source PDF download
endpoint is provided. A job is processed only when a worker is run; no
automatic retry or redrive policy is provided.

## Current boundary

This is a local development service. Its SQLite/CAS persistence is local only.
It has no authentication, authorization, tenant isolation, encryption-at-rest
claim, rate limiting, wildcard CORS, distributed transaction guarantee, or
public deployment hardening. A successful health response or PDF inspection
does not prove product acceptance, real-book end-to-end acceptance, Android
integration, or any downstream media/game acceptance gate.
