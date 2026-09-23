# BIE API

This directory contains the first stateless HTTP boundary for My Book Intelligence
Engine. Canonical engines remain under `bie/`; the API delegates PDF inspection to
`bie.document_intelligence.real_pdf_toc_runtime.inspect_real_pdf_toc` and does not
duplicate Document Intelligence logic.

## Endpoints

- `GET /healthz` reports HTTP process liveness only.
- `GET /v1/capabilities` reports the service's current bounded capabilities.
- `POST /v1/documents/inspect` accepts a raw `application/pdf` request body and
  returns the Task 016 safe deterministic representation.

The inspection endpoint accepts at most 25 MiB and fails closed for unsupported
media types, empty bodies, oversized requests, and PDFs the governed runtime cannot
inspect. It does not accept multipart form data and never returns raw book text,
heading text, outline titles, PDF bytes, or local paths.

## Run locally

From the repository root after installing the API and Document Intelligence extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[document-intelligence,document-intelligence-layout,api]"
.\.venv\Scripts\python.exe scripts\run_bie_api.py
```

The default bind is `127.0.0.1:8000`, with reload and debug behavior disabled.

## Current boundary

This is a local development service. It has no persistence, authentication,
authorization, asynchronous jobs, queues, rate limiting, wildcard CORS, or public
deployment hardening. A successful health response or PDF inspection does not prove
product acceptance, real-book end-to-end acceptance, Android integration, or any
downstream media/game acceptance gate.
