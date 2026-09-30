from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from bie.prerequisite_intelligence.graph import Edge, build_graph
from bie.product_app_v1.concept_graph_viewer import concept_graph_view, render_concept_graph
from bie.product_app_v1.context import OperatorContext
from bie.product_app_v1.failure_view import FailureViewService, render_failure_view
from bie.product_app_v1.models import OperatorConflict, OperatorError
from bie.product_app_v1.prerequisite_graph_viewer import (
    prerequisite_graph_view,
    render_prerequisite_graph,
)
from bie.product_app_v1.retry import RetryService
from bie.product_app_v1.run_control import RunControlService
from bie.product_app_v1.run_create import create_run
from bie.product_app_v1.run_status import RunStatusService
from bie.product_app_v1.source_import import SourceImportService
from bie.product_app_v1.source_validation import MAX_SOURCE_BYTES, render_source_validation, render_source_validation_shell, validate_pdf_source
from bie.product_app_v1.stage_timeline import StageTimelineService
from apps.web.section18_views import render_run_status, render_timeline

router = APIRouter(prefix="/v1/operator", tags=["section18-operator"])
MAX_JSON_BYTES = 2 * 1024 * 1024


class CreateRunBody(BaseModel):
    create_key: str


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code}})


def _context() -> OperatorContext:
    root = os.environ.get("BIE_DATA_ROOT")
    if not root:
        raise OperatorError("bie_data_root_required")
    return OperatorContext(Path(root))


def _enabled() -> bool:
    return os.environ.get("BIE_SECTION18_LOCAL_OPERATOR") == "1"


def _guard() -> JSONResponse | None:
    if not _enabled():
        return _error(503, "section18_operator_disabled")
    return None


async def _bounded_body(request: Request, limit: int) -> bytes:
    data = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        if len(data) + len(chunk) > limit:
            raise OperatorError("request_too_large")
        data.extend(chunk)
    return bytes(data)


async def _json_body(request: Request) -> object:
    raw = await _bounded_body(request, MAX_JSON_BYTES)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise OperatorError("invalid_json") from exc


@router.post("/runs")
async def create_operator_run(body: CreateRunBody):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return JSONResponse(create_run(_context().operator, body.create_key), status_code=201)
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(400, str(exc))


@router.post("/runs/{run_id}/source")
async def import_source(run_id: str, request: Request):
    if (blocked := _guard()) is not None:
        return blocked
    if request.headers.get("content-type", "").partition(";")[0].lower() != "application/pdf":
        return _error(415, "unsupported_media_type")
    try:
        payload = await _bounded_body(request, MAX_SOURCE_BYTES)
        name = request.headers.get("x-source-name", "Selected PDF")
        result = SourceImportService(_context()).import_pdf(
            run_id, payload, display_name=name, media_type="application/pdf"
        )
        return JSONResponse(result, status_code=202 if result["validation"]["accepted"] else 422)
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        code = str(exc)
        return _error(413 if code == "request_too_large" else 400, code)


@router.get("/source-validation-ui", response_class=HTMLResponse)
async def source_validation_ui():
    if (blocked := _guard()) is not None:
        return blocked
    return HTMLResponse(render_source_validation_shell())


@router.post("/source-validation", response_class=HTMLResponse)
async def source_validation_page(request: Request):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        payload = await _bounded_body(request, MAX_SOURCE_BYTES)
        validation = validate_pdf_source(
            payload,
            media_type=request.headers.get("content-type", ""),
        )
        return HTMLResponse(
            render_source_validation(
                validation,
                display_name=request.headers.get("x-source-name", "Selected PDF"),
            ),
            status_code=200 if validation.accepted else 422,
        )
    except OperatorError as exc:
        return _error(413 if str(exc) == "request_too_large" else 400, str(exc))


@router.get("/runs/{run_id}")
async def operator_status(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return RunStatusService(_context()).status(run_id)
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.get("/runs/{run_id}/status-view", response_class=HTMLResponse)
async def operator_status_view(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return HTMLResponse(render_run_status(RunStatusService(_context()).status(run_id)))
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.get("/runs/{run_id}/timeline")
async def operator_timeline(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return StageTimelineService(_context()).timeline(run_id)
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.get("/runs/{run_id}/timeline-view", response_class=HTMLResponse)
async def operator_timeline_view(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return HTMLResponse(render_timeline(StageTimelineService(_context()).timeline(run_id)))
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.get("/runs/{run_id}/failure")
async def operator_failure(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return FailureViewService(_context()).failure(run_id)
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.get("/runs/{run_id}/failure-view", response_class=HTMLResponse)
async def operator_failure_view(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return HTMLResponse(render_failure_view(FailureViewService(_context()).failure(run_id)))
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(404 if str(exc) == "run_not_found" else 400, str(exc))


@router.post("/runs/{run_id}/retry")
async def operator_retry(run_id: str):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        return RetryService(_context()).retry(run_id)
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(400, str(exc))


@router.post("/runs/{run_id}/{action}")
async def operator_control(run_id: str, action: str):
    if (blocked := _guard()) is not None:
        return blocked
    service = RunControlService(_context())
    try:
        if action == "pause":
            return service.pause(run_id)
        if action == "resume":
            return service.resume(run_id)
        if action == "cancel":
            return service.cancel(run_id)
        return _error(404, "unknown_control_action")
    except OperatorConflict as exc:
        return _error(409, str(exc))
    except OperatorError as exc:
        return _error(400, str(exc))


@router.post("/viewers/concept-graph", response_class=HTMLResponse)
async def concept_graph_page(request: Request):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        body = await _json_body(request)
        if not isinstance(body, dict) or not isinstance(body.get("graph"), dict):
            raise OperatorError("concept_graph_payload_required")
        view = concept_graph_view(
            body["graph"],
            label_filter=body.get("label_filter"),
            relation_type=body.get("relation_type"),
            min_confidence=body.get("min_confidence", 0.0),
        )
        return HTMLResponse(render_concept_graph(view))
    except OperatorError as exc:
        return _error(400, str(exc))


@router.post("/viewers/prerequisite-graph", response_class=HTMLResponse)
async def prerequisite_graph_page(request: Request):
    if (blocked := _guard()) is not None:
        return blocked
    try:
        body = await _json_body(request)
        if not isinstance(body, dict):
            raise OperatorError("prerequisite_graph_payload_required")
        nodes = body.get("nodes")
        edges = body.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise OperatorError("prerequisite_graph_payload_required")
        if any(not isinstance(e, dict) for e in edges):
            raise OperatorError("prerequisite_edge_must_be_mapping")
        graph = build_graph(
            [str(x) for x in nodes],
            [
                Edge(str(e["prerequisite"]), str(e["dependent"]), float(e.get("confidence", 1.0)))
                for e in edges
            ],
        )
        view = prerequisite_graph_view(
            graph,
            labels=body.get("labels"),
            source_refs=body.get("source_refs"),
        )
        return HTMLResponse(render_prerequisite_graph(view))
    except (OperatorError, ValueError, KeyError, TypeError) as exc:
        return _error(400, str(exc) or "invalid_prerequisite_graph")


def install_section18_routes(app) -> None:
    """Explicit opt-in mounting. Importing this module does not mutate canonical app."""
    app.include_router(router)
