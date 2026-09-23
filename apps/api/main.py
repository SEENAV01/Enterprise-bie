"""Local HTTP boundary for synchronous and durable PDF inspection."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bie.document_intelligence.real_pdf_toc_runtime import (
    RealPdfTocRuntimeError,
    inspect_real_pdf_toc,
)
from .job_service import (
    IdempotencyConflict,
    InvalidIdempotencyKey,
    JobFailed,
    JobNotFound,
    PdfInspectionJobService,
    ResultNotReady,
    validate_idempotency_key,
)


API_VERSION = "v1"
API_SCHEMA_VERSION = "1.0"
MAX_PDF_BYTES = 25 * 1024 * 1024


class PayloadTooLargeError(ValueError):
    """Raised as soon as a streamed request exceeds the configured limit."""


app = FastAPI(
    title="My Book Intelligence Engine API",
    version=API_SCHEMA_VERSION,
    docs_url=None,
    redoc_url=None,
)


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def _media_type(request: Request) -> str:
    return request.headers.get("content-type", "").partition(";")[0].strip().lower()


async def _read_bounded_body(request: Request, *, max_bytes: int) -> bytes:
    payload = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        if len(payload) + len(chunk) > max_bytes:
            raise PayloadTooLargeError("request body exceeds configured limit")
        payload.extend(chunk)
    return bytes(payload)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Report HTTP process liveness only."""

    return {"status": "ok", "service": "bie-api", "api_version": API_VERSION}


@app.get("/v1/capabilities")
async def capabilities() -> dict[str, object]:
    """Return truthful capabilities for this bounded development service."""

    return {
        "api_version": API_VERSION,
        "document_inspection": "native_pdf_toc_v1",
        "stateless": False,
        "persistence": True,
        "async_jobs": True,
        "authentication": False,
        "product_accepted": False,
        "persistence_backend": "local_sqlite_cas_v1",
        "worker_mode": "local_manual_run_once_v1",
    }


@app.post("/v1/documents/inspect")
async def inspect_document(request: Request) -> JSONResponse:
    """Inspect a bounded raw PDF body through the verified Task 016 runtime."""

    if _media_type(request) != "application/pdf":
        return _error(415, "unsupported_media_type", "Content-Type must be application/pdf")

    try:
        payload = await _read_bounded_body(request, max_bytes=MAX_PDF_BYTES)
    except PayloadTooLargeError:
        return _error(413, "payload_too_large", "PDF payload exceeds 25 MiB limit")
    except Exception:
        return _error(500, "internal_error", "Internal service error")

    if not payload:
        return _error(400, "empty_body", "PDF request body is empty")

    try:
        inspection = inspect_real_pdf_toc(payload)
        safe_result = inspection.to_safe_dict()
    except RealPdfTocRuntimeError:
        return _error(422, "pdf_inspection_failed", "PDF inspection failed")
    except Exception:
        return _error(500, "internal_error", "Internal service error")

    return JSONResponse(
        status_code=200,
        content={
            "api_schema_version": API_SCHEMA_VERSION,
            "result": safe_result,
        },
    )


def _job_service() -> PdfInspectionJobService:
    return PdfInspectionJobService()


@app.post("/v1/jobs/document-inspection")
async def submit_document_inspection(request: Request) -> JSONResponse:
    if _media_type(request) != "application/pdf":
        return _error(415, "unsupported_media_type", "Content-Type must be application/pdf")
    try:
        key = validate_idempotency_key(request.headers.get("idempotency-key"))
    except InvalidIdempotencyKey as exc:
        code = str(exc)
        message = "Idempotency-Key is required" if code == "idempotency_key_required" else "Invalid Idempotency-Key"
        return _error(400, code, message)
    try:
        payload = await _read_bounded_body(request, max_bytes=MAX_PDF_BYTES)
    except PayloadTooLargeError:
        return _error(413, "payload_too_large", "PDF payload exceeds 25 MiB limit")
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    if not payload:
        return _error(400, "empty_body", "PDF request body is empty")
    service = None
    try:
        service = _job_service()
        job = service.submit(payload, key)
    except IdempotencyConflict:
        return _error(409, "idempotency_conflict", "Idempotency-Key conflicts with an existing PDF")
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=202, content={"api_schema_version": API_SCHEMA_VERSION, "job": job})


@app.get("/v1/jobs/{job_id}")
async def job_status(job_id: str) -> JSONResponse:
    service = None
    try:
        service = _job_service()
        status = service.status(job_id)
    except JobNotFound:
        return _error(404, "job_not_found", "Job not found")
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content={"api_schema_version": API_SCHEMA_VERSION, "job": status})


@app.get("/v1/jobs/{job_id}/result")
async def job_result(job_id: str) -> JSONResponse:
    service = None
    try:
        service = _job_service()
        result = service.result(job_id)
    except JobNotFound:
        return _error(404, "job_not_found", "Job not found")
    except ResultNotReady:
        return _error(409, "result_not_ready", "Job result is not ready")
    except JobFailed:
        return _error(409, "job_failed", "Job failed")
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content={
        "api_schema_version": API_SCHEMA_VERSION,
        "job_id": job_id,
        "result": result,
    })
