"""Section 18 bounded operator API routes."""
from fastapi import APIRouter,Request
from fastapi.responses import HTMLResponse,JSONResponse
from bie.product_app import GraphArtifactError,GraphArtifactViewer,OperatorError,OperatorRunService
from bie.product_app.html_views import graph_html,source_validation_html
from .job_service import data_root_from_env
router=APIRouter(prefix="/v1/operator",tags=["operator"])
def _service():return OperatorRunService(data_root_from_env())
def _error(status,code,message):return JSONResponse(status_code=status,content={"error":{"code":code,"message":message}})
async def _json(request):
    try:b=await request.json()
    except Exception as exc:raise OperatorError("invalid json body") from exc
    if type(b) is not dict:raise OperatorError("json object required")
    return b
@router.post("/runs")
async def create_run(request:Request):
    try:
        b=await _json(request);return JSONResponse(status_code=201,content=_service().create_run(b.get("config_hash"),b.get("profile","pdf_inspection_v1")))
    except OperatorError as exc:return _error(400,"operator_request_invalid",str(exc))
@router.post("/runs/{run_id}/source")
async def import_source(run_id:str,request:Request):
    try:
        data=await request.body();name=request.headers.get("x-bie-filename","");mt=request.headers.get("content-type","").partition(";")[0].strip().lower()
        return JSONResponse(status_code=201,content=_service().import_source(run_id,name,mt,data))
    except OperatorError as exc:return _error(422,"source_rejected",str(exc))
@router.get("/runs/{run_id}")
async def run_status(run_id:str):
    try:return JSONResponse(status_code=200,content=_service().status(run_id))
    except OperatorError as exc:return _error(404,"run_not_found",str(exc))
@router.get("/runs/{run_id}/timeline")
async def run_timeline(run_id:str):
    try:return JSONResponse(status_code=200,content=_service().timeline(run_id))
    except OperatorError as exc:return _error(404,"run_not_found",str(exc))
@router.get("/runs/{run_id}/failures")
async def run_failures(run_id:str):
    try:return JSONResponse(status_code=200,content=_service().failures(run_id))
    except OperatorError as exc:return _error(404,"run_not_found",str(exc))
@router.get("/runs/{run_id}/source-validation")
async def source_validation(run_id:str,request:Request):
    try:v=_service().source_validation(run_id)
    except OperatorError as exc:return _error(404,"run_not_found",str(exc))
    return HTMLResponse(source_validation_html(v)) if "text/html" in request.headers.get("accept","") else JSONResponse(status_code=200,content=v)
@router.post("/runs/{run_id}/retry")
async def retry_stage(run_id:str,request:Request):
    try:
        b=await _json(request);return JSONResponse(status_code=202,content=_service().retry_stage(run_id,b.get("stage_id"),b.get("reason")))
    except OperatorError as exc:return _error(409,"retry_rejected",str(exc))
@router.post("/runs/{run_id}/control")
async def control_run(run_id:str,request:Request):
    try:
        b=await _json(request);return JSONResponse(status_code=202,content=_service().request_control(run_id,b.get("action"),b.get("reason")))
    except OperatorError as exc:return _error(409,"control_rejected",str(exc))
@router.get("/runs/{run_id}/graphs/{kind}/{artifact_id}")
async def graph_view(run_id:str,kind:str,artifact_id:str,request:Request):
    s=_service()
    try:
        s._load(run_id);v=GraphArtifactViewer(s.persistence,s.cas).load(run_id,artifact_id,kind)
    except (OperatorError,GraphArtifactError) as exc:return _error(422,"graph_unavailable",str(exc))
    if "text/html" in request.headers.get("accept",""):
        return HTMLResponse(graph_html("Concept graph" if kind=="concept" else "Prerequisite graph",v))
    return JSONResponse(status_code=200,content=v)
