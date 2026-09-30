from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from apps.api.job_service import (
    IdempotencyConflict,
    InvalidIdempotencyKey,
    validate_idempotency_key,
)
from bie.app_product.contracts import MAX_SOURCE_BYTES, ProductContractError, validate_pdf_source
from bie.app_product.graph_views import GraphViewError, GraphViewService
from bie.app_product.operator_service import OperatorConflict, OperatorJobService


router = APIRouter(prefix="/v1/app", tags=["section18-operator"])


class PayloadTooLarge(ValueError):
    pass


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def _read_bounded(request: Request) -> bytes:
    payload = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        if len(payload) + len(chunk) > MAX_SOURCE_BYTES:
            raise PayloadTooLarge("source too large")
        payload.extend(chunk)
    return bytes(payload)


def _media_type(request: Request) -> str:
    return request.headers.get("content-type", "").partition(";")[0].strip().lower()


def _service() -> OperatorJobService:
    return OperatorJobService()


def _operator_error(exc: OperatorConflict) -> JSONResponse:
    code = str(exc)
    if code == "job_not_found":
        return _error(404, code, "Run not found")
    return _error(409, code, "Requested operator action is not valid for the current run state")


@router.post("/sources/validate")
async def validate_source(request: Request) -> JSONResponse:
    try:
        payload = await _read_bounded(request)
    except PayloadTooLarge:
        return JSONResponse(
            status_code=200,
            content=validate_pdf_source(
                b"x" * (MAX_SOURCE_BYTES + 1),
                media_type=_media_type(request) or "application/octet-stream",
            ).to_safe_dict(),
        )
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    try:
        result = validate_pdf_source(
            payload,
            media_type=_media_type(request) or "application/octet-stream",
        )
    except ProductContractError:
        return _error(400, "invalid_source_request", "Invalid source-validation request")
    return JSONResponse(status_code=200, content=result.to_safe_dict())


@router.post("/runs")
async def create_run(request: Request) -> JSONResponse:
    try:
        key = validate_idempotency_key(request.headers.get("idempotency-key"))
    except InvalidIdempotencyKey as exc:
        return _error(400, str(exc), "A valid Idempotency-Key is required")
    try:
        payload = await _read_bounded(request)
    except PayloadTooLarge:
        return _error(413, "source_too_large", "PDF source exceeds the configured limit")
    except Exception:
        return _error(500, "internal_error", "Internal service error")

    validation = validate_pdf_source(
        payload,
        media_type=_media_type(request) or "application/octet-stream",
    )
    if not validation.valid:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "source_validation_failed",
                    "message": "Source validation failed",
                },
                "validation": validation.to_safe_dict(),
            },
        )

    service = None
    try:
        service = _service()
        run = service.submit(payload, key)
    except IdempotencyConflict:
        return _error(409, "idempotency_conflict", "Idempotency-Key conflicts with an existing source")
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=202, content={
        "api_schema_version": "bie.app.api/1",
        "run": run,
        "validation": validation.to_safe_dict(),
    })


@router.get("/runs/{job_id}")
async def run_status(job_id: str) -> JSONResponse:
    service = None
    try:
        service = _service()
        value = service.status(job_id)
    except OperatorConflict as exc:
        return _operator_error(exc)
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content=value)


@router.get("/runs/{job_id}/timeline")
async def stage_timeline(job_id: str) -> JSONResponse:
    service = None
    try:
        service = _service()
        value = service.timeline(job_id)
    except OperatorConflict as exc:
        return _operator_error(exc)
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content=value)


@router.get("/runs/{job_id}/failure")
async def failure_view(job_id: str) -> JSONResponse:
    service = None
    try:
        service = _service()
        value = service.failure_view(job_id)
    except OperatorConflict as exc:
        return _operator_error(exc)
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content=value)


async def _control(job_id: str, action: str) -> JSONResponse:
    service = None
    try:
        service = _service()
        method = getattr(service, action)
        value = method(job_id)
    except OperatorConflict as exc:
        return _operator_error(exc)
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content=value)


@router.post("/runs/{job_id}/retry")
async def retry_run(job_id: str) -> JSONResponse:
    return await _control(job_id, "retry")


@router.post("/runs/{job_id}/pause")
async def pause_run(job_id: str) -> JSONResponse:
    return await _control(job_id, "pause")


@router.post("/runs/{job_id}/resume")
async def resume_run(job_id: str) -> JSONResponse:
    return await _control(job_id, "resume")


@router.post("/runs/{job_id}/cancel")
async def cancel_run(job_id: str) -> JSONResponse:
    return await _control(job_id, "cancel")


@router.get("/runs/{job_id}/graphs/{kind}")
async def graph_view(
    job_id: str,
    kind: str,
    artifact_id: str = Query(..., min_length=1, max_length=256),
) -> JSONResponse:
    service = None
    try:
        service = _service()
        value = GraphViewService(service.persistence, service.cas).view(
            job_id,
            artifact_id,
            kind,
        )
    except GraphViewError as exc:
        code = str(exc)
        if code in {"artifact_not_found", "cross_run_artifact"}:
            return _error(404, "graph_artifact_not_found", "Graph artifact not found")
        return _error(422, code, "Graph artifact cannot be rendered safely")
    except OperatorConflict as exc:
        return _operator_error(exc)
    except Exception:
        return _error(500, "internal_error", "Internal service error")
    finally:
        if service is not None:
            service.close()
    return JSONResponse(status_code=200, content=value)
