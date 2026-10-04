"""Local operator HTTP application over canonical BIE, with explicit credentials."""
from pathlib import Path
from urllib.parse import urlsplit
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool
from .contracts import OperatorError, require, strict_json, private_path

WEB = Path(__file__).resolve().parents[1] / 'web' / 'operator'

def create_app(service):
    from .artifacts import ProductArtifacts
    artifacts=ProductArtifacts(service)
    from .previews import Previews
    previews=Previews(service)
    from .quality import Quality
    quality=Quality(service)
    from .assurance import Assurance
    assurance=Assurance(service)
    administration=service.administration
    app = FastAPI(title='BIE local operator',docs_url=None,redoc_url=None,openapi_url=None)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]'])
    app.state.operator_service = service
    app.state.previews = previews

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request,exc):
        return JSONResponse({'error':{'code':'invalid_request','message':'Operator action not completed'}},status_code=400)

    @app.middleware('http')
    async def safe_boundary(request,call_next):
        try:
            origin = request.headers.get('origin')
            if origin and request.method not in ('GET','HEAD'):
                expected = f'{request.url.scheme}://{request.headers.get("host","")}'
                require(origin == expected,'origin_rejected',403)
            response = await call_next(request)
        except OperatorError as e:
            response = JSONResponse({'error':{'code':e.code,'message':'Operator action not completed'}},status_code=e.status)
        except Exception:
            # Neither paths nor upstream exception strings are logged/returned.
            response = JSONResponse({'error':{'code':'internal_error','message':'Internal operator service error'}},status_code=500)
        if request.url.path.startswith('/_preview/') and response.status_code==200:
            # Opaque sandbox origin needs scoped CORS for its own ES modules;
            # this applies only to expiring package grants, never operator APIs.
            prefix=f'{request.url.scheme}://{request.headers.get("host","")}/_preview/{request.path_params["ticket"]}/'
            response.headers['Content-Security-Policy'] = f"sandbox allow-scripts; default-src 'none'; script-src {prefix}; style-src {prefix}; img-src {prefix} data:; media-src {prefix}; connect-src 'none'; worker-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
            response.headers['Access-Control-Allow-Origin']='null'
            response.headers['Cross-Origin-Resource-Policy']='cross-origin'
            response.headers['X-Frame-Options']='SAMEORIGIN'
        else:
            response.headers['Content-Security-Policy'] = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; media-src blob:; frame-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
            response.headers['X-Frame-Options']='DENY'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Cache-Control']='no-store'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        return response

    def principal(request,permission):
        header = request.headers.get('authorization','')
        require(header.startswith('Bearer ') and header.count(' ')==1,'unauthorized',401)
        p = service.credentials.authenticate(header[7:])
        service.authorize(p,permission)
        return p

    async def body_json(request):
        require(request.headers.get('content-type','').split(';',1)[0].strip().lower()=='application/json',
                'unsupported_media_type',415)
        raw = bytearray()
        async for chunk in request.stream():
            require(len(raw)+len(chunk)<=16384,'payload_too_large',413); raw.extend(chunk)
        return strict_json(bytes(raw))

    @app.get('/healthz')
    def health(): return dict(status='ok',service='bie-local-operator',product_accepted=False)

    @app.get('/operator/v1/workspace')
    def workspace(request:Request):
        # Authorization and catalogue integrity are independent of any run's
        # native health. A partial run must not lock out its recovery controls.
        p=principal(request,'read')
        with service.catalog.tx(read_only=True):service.authorize(p,'read')
        return dict(status='AUTHORIZED_WORKSPACE',run_health_checked=False,
                    tenant_scoped=True,product_accepted=False)

    @app.get('/')
    def home(): return FileResponse(WEB/'index.html',media_type='text/html')

    @app.get('/static/{name}')
    def static(name:str):
        require(name in ('operator.js','operator.css','viewers.js','viewers.css','previews.js','quality.js','assurance.js','administration.js','governance.js'),'resource_not_found',404)
        return FileResponse(private_path(WEB,name),media_type='text/javascript' if name.endswith('.js') else 'text/css')

    @app.post('/operator/v1/sources')
    async def upload(request:Request):
        p=principal(request,'source')
        media=request.headers.get('content-type','').split(';',1)[0].strip().lower()
        require(media=='application/pdf','unsupported_media_type',415)
        declared=request.headers.get('content-length')
        if declared:
            require(declared.isdecimal(),'invalid_content_length',400)
            require(int(declared)<=service.limit,'payload_too_large',413)
        count=0
        # Filenames/paths from clients are deliberately never used.
        with service.staging() as stage:
            async for chunk in request.stream():
                require(count+len(chunk)<=service.limit,'payload_too_large',413)
                stage.write(chunk); count+=len(chunk)
            require(count>0,'empty_body',400)
            stage.flush(); stage.seek(0)
            data=stage.read(service.limit+1)
        return await run_in_threadpool(service.import_pdf,p,data)

    @app.get('/operator/v1/sources/{source_id}')
    def source(source_id:str,request:Request): return service.source(principal(request,'read'),source_id)

    @app.post('/operator/v1/runs',status_code=202)
    async def create(request:Request):
        p=principal(request,'create'); body=await body_json(request)
        require(type(body) is dict and set(body) in ({'source_id','config','idempotency_key'},
            {'source_id','config','idempotency_key','policy_binding'}),'invalid_run_request',400)
        return await run_in_threadpool(service.create,p,body['source_id'],body['config'],body['idempotency_key'],
                                      policy_binding=body.get('policy_binding'))

    @app.get('/operator/v1/runs')
    def runs(request:Request,offset:int=0,limit:int=25): return service.list_runs(principal(request,'read'),offset,limit)

    @app.get('/operator/v1/runs/{run_id}')
    def status(run_id:str,request:Request): return service.status(principal(request,'read'),run_id)

    @app.get('/operator/v1/runs/{run_id}/timeline')
    def timeline(run_id:str,request:Request,after:int=0,limit:int=100):
        return service.timeline(principal(request,'read'),run_id,after,limit)

    @app.get('/operator/v1/runs/{run_id}/failure')
    def failure(run_id:str,request:Request): return service.failure(principal(request,'read'),run_id)

    @app.get('/operator/v1/runs/{run_id}/result')
    def result(run_id:str,request:Request): return service.result(principal(request,'read'),run_id)

    @app.get('/operator/v1/runs/{run_id}/evidence/{evidence_id}')
    def evidence(run_id:str,evidence_id:str,request:Request):
        return service.evidence(principal(request,'read'),run_id,evidence_id)

    @app.post('/operator/v1/runs/{run_id}/control')
    async def control(run_id:str,request:Request):
        p=principal(request,'control'); body=await body_json(request)
        require(type(body) is dict and set(body)=={'action','expected_revision'},'invalid_control_request',400)
        return await run_in_threadpool(service.control,p,run_id,body['action'],body['expected_revision'])

    @app.post('/operator/v1/runs/{run_id}/retry',status_code=202)
    async def retry(run_id:str,request:Request):
        p=principal(request,'retry'); body=await body_json(request)
        require(type(body) is dict and set(body)=={'idempotency_key'},'invalid_retry_request',400)
        return await run_in_threadpool(service.retry,p,run_id,body['idempotency_key'])

    @app.get('/operator/v1/runs/{run_id}/graphs/{kind}')
    def graph(run_id:str,kind:str,request:Request): return service.graph(principal(request,'read'),run_id,kind)

    @app.get('/operator/v1/runs/{run_id}/views/{kind}')
    def view(run_id:str,kind:str,request:Request):return artifacts.view(principal(request,'read'),run_id,kind)

    @app.get('/operator/v1/runs/{run_id}/quality/{kind}')
    def quality_view(run_id:str,kind:str,request:Request,offset:int=0,limit:int=10):
        return quality.get(principal(request,'read'),run_id,kind,offset,limit)

    @app.get('/operator/v1/runs/{run_id}/assurance/{kind}')
    def assurance_view(run_id:str,kind:str,request:Request,offset:int=0,limit:int=10):
        return assurance.get(principal(request,'read'),run_id,kind,offset,limit)

    @app.get('/operator/v1/admin/providers')
    def providers(request:Request,after:str|None=None,limit:int=25):
        return administration.providers(principal(request,'admin_read'),after,limit)

    @app.get('/operator/v1/governance/{kind}')
    def configuration_list(kind:str,request:Request,after:str|None=None,limit:int=25):
        return service.governance.list(principal(request,'admin_read'),kind,after,limit)

    @app.post('/operator/v1/governance/{kind}/{config_id}/versions')
    async def configuration_save(kind:str,config_id:str,request:Request):
        p=principal(request,'admin_read');body=await body_json(request)
        require(type(body) is dict and set(body)=={'configuration','expected_revision','idempotency_key'},'invalid_configuration_request',400)
        result=await run_in_threadpool(service.governance.save,p,kind,config_id,body['configuration'],body['expected_revision'],body['idempotency_key'])
        return service.governance.public(result)

    @app.get('/operator/v1/governance/{kind}/{config_id}/history')
    def configuration_history(kind:str,config_id:str,request:Request,after_revision:int=0,limit:int=25):
        return service.governance.history(principal(request,'admin_read'),kind,config_id,after_revision,limit)

    @app.get('/operator/v1/governance/{kind}/{config_id}/diff')
    def configuration_diff(kind:str,config_id:str,request:Request,left:int,right:int):
        return service.governance.diff(principal(request,'admin_read'),kind,config_id,left,right)

    @app.post('/operator/v1/governance/{kind}/{config_id}/activate')
    async def configuration_activate(kind:str,config_id:str,request:Request):
        p=principal(request,'admin_read');body=await body_json(request)
        require(type(body) is dict and set(body)=={'revision','configuration_sha256','expected_active_sha256','idempotency_key'},
                'invalid_activation_request',400)
        return await run_in_threadpool(service.governance.activate,p,kind,config_id,body['revision'],body['configuration_sha256'],
                                      body['expected_active_sha256'],body['idempotency_key'])

    @app.get('/operator/v1/admin/audit')
    def audit_view(request:Request,after:int=0,limit:int=25,action:str|None=None,target:str|None=None):
        return service.governance.audit(principal(request,'admin_read'),after,limit,action,target)

    @app.get('/operator/v1/admin/providers/{config_id}/history')
    def provider_history(config_id:str,request:Request,after_revision:int=0,limit:int=25):
        return administration.provider_history(principal(request,'admin_read'),config_id,after_revision,limit)

    @app.post('/operator/v1/admin/providers/{config_id}/enabled')
    async def provider_enabled(config_id:str,request:Request):
        p=principal(request,'admin_config');body=await body_json(request)
        require(type(body) is dict and set(body)=={'enabled','expected_revision','idempotency_key'},'invalid_provider_update',400)
        return administration.set_provider_enabled(p,config_id,body['enabled'],body['expected_revision'],body['idempotency_key'])

    @app.get('/operator/v1/admin/workers')
    def workers(request:Request,after:str|None=None,limit:int=25):
        return administration.workers(principal(request,'admin_read'),after,limit)

    @app.get('/operator/v1/admin/queue')
    def queue_view(request:Request,after:str|None=None,limit:int=25,state:str|None=None):
        return administration.queue(principal(request,'admin_read'),after,limit,state)

    @app.post('/operator/v1/admin/workers/{worker_id}/reconcile')
    async def reconcile_worker(worker_id:str,request:Request):
        p=principal(request,'admin_recover');body=await body_json(request)
        require(type(body) is dict and set(body)=={'expected_record_sha256','idempotency_key'},
                'invalid_worker_recovery',400)
        return await run_in_threadpool(administration.reconcile_worker,p,worker_id,
                                      body['expected_record_sha256'],body['idempotency_key'])

    @app.get('/operator/v1/admin/dead-letters/{run_id}')
    def dead_letter(run_id:str,request:Request,after_sequence:int=0,limit:int=25):
        return administration.dead_letter(principal(request,'admin_read'),run_id,after_sequence,limit)

    @app.post('/operator/v1/admin/dead-letters/{run_id}/retry',status_code=202)
    async def recover_dead_letter(run_id:str,request:Request):
        p=principal(request,'admin_recover');body=await body_json(request)
        require(type(body) is dict and set(body)=={'idempotency_key','expected_revision','expected_queue_digest'},
                'invalid_recovery_request',400)
        return await run_in_threadpool(administration.recover_dead_letter,p,run_id,body['idempotency_key'],
                                      body['expected_revision'],body['expected_queue_digest'])

    @app.get('/operator/v1/runs/{run_id}/artifacts')
    def browse(run_id:str,request:Request,offset:int=0,limit:int=25,artifact_type:str|None=None,evidence_only:bool=False):
        return artifacts.browse(principal(request,'read'),run_id,offset,limit,artifact_type,evidence_only)

    @app.get('/operator/v1/runs/{run_id}/artifacts/{artifact_id}/lineage')
    def lineage(run_id:str,artifact_id:str,request:Request,max_nodes:int=128):
        return artifacts.lineage(principal(request,'read'),run_id,artifact_id,max_nodes)

    @app.get('/operator/v1/runs/{run_id}/artifacts/{artifact_id}/evidence')
    def artifact_evidence(run_id:str,artifact_id:str,request:Request):
        return artifacts.evidence_detail(principal(request,'read'),run_id,artifact_id)

    @app.get('/operator/v1/runs/{run_id}/artifacts/{artifact_id}/code')
    def code(run_id:str,artifact_id:str,request:Request,offset:int=0,limit:int=100):
        return artifacts.code(principal(request,'read'),run_id,artifact_id,offset,limit)

    @app.get('/operator/v1/runs/{run_id}/previews/{kind}')
    def preview(run_id:str,kind:str,request:Request):return previews.get(principal(request,'read'),run_id,kind)

    @app.api_route('/operator/v1/runs/{run_id}/render/media',methods=['GET','HEAD'])
    def media(run_id:str,request:Request):
        p=principal(request,'read')
        try:
            raw,status,headers=previews.media(p,run_id,request.headers.get('range') if request.method=='GET' else None,request.headers.get('if-range'))
        except OperatorError as e:
            if e.status!=416:raise
            data,_,_=previews.media(p,run_id)
            return JSONResponse({'error':{'code':e.code,'message':'Operator action not completed'}},status_code=416,
                                headers={'Content-Range':f'bytes */{len(data)}','Accept-Ranges':'bytes'})
        return Response(raw if request.method=='GET' else b'',status_code=status,headers=headers,media_type='video/mp4')

    @app.post('/operator/v1/runs/{run_id}/game/preview-grant')
    async def preview_grant(run_id:str,request:Request):
        p=principal(request,'read');body=await body_json(request)
        require(body=={},'invalid_preview_request',400)
        return previews.grant(p,run_id,request.headers['authorization'][7:])

    @app.post('/operator/v1/preview-grants/revoke')
    async def revoke_grants(request:Request):
        p=principal(request,'read');require(await body_json(request)=={},'invalid_preview_request',400)
        previews.revoke(p);return dict(status='REVOKED')

    @app.get('/_preview/{ticket}/{path:path}')
    def preview_file(ticket:str,path:str,request:Request):
        raw,media_type=previews.game_file(ticket,path)
        return Response(raw,media_type=media_type)

    # No HTTP worker-control or arbitrary producer/executor registration endpoint.
    return app
