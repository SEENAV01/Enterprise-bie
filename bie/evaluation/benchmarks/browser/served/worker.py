"""H5-004: real HTTP/module browser execution. Respect administrator policies.
There is intentionally no set_content, eval, data URL, proxy or policy fallback.
"""
from pathlib import Path
import sys,json,hashlib,base64
sys.path.insert(0,str(Path(__file__).resolve().parents[5]));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import BenchmarkError,canonical_json,strict_loads
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits,candidate
from bie.evaluation.benchmarks.browser.served.lifecycle import run_steps
from bie.evaluation.benchmarks.browser.served.contracts import reference,binding
from bie.evaluation.benchmarks.browser.served.server import serve
from bie.evaluation.benchmarks.browser.served.origin import route_path
from bie.evaluation.benchmarks.browser.served.lifecycle import navigate
from bie.evaluation.benchmarks.browser.served.accessibility import collect as collect_ax

def collect(config):
    from playwright.sync_api import sync_playwright
    limits=BrowserLimits(**config['limits']).validate()
    r=reference(config['reference'],limits=limits);c=candidate(config['candidate'],limits);binding(r,c)
    if c['origin_kind']!='AUTHORED_FIXTURE':raise BenchmarkError('HTTP_NONAUTHORED_RUNTIME_NOT_ADMITTED')
    assets={}
    for row in c['files']:
        raw=(Path(config['snapshot_root'])/row['path']).read_bytes()
        if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise BenchmarkError('HTTP_SNAPSHOT_CHANGED')
        assets[row['path']]=raw
    policy=r['http_policy'];runs=[]
    result={'status':'BLOCKED','transport':'REAL_LOOPBACK_HTTP_MODULE_APP',
       'network_mode':'BROWSER_ROUTE_ALLOWLIST_NOT_OS_CONTAINMENT',
       'hostile_code_sandbox_verified':False,'trusted_fixture_execution_only':True,
       'chromium_sandbox_requested':not config['allow_unsandboxed_diagnostic'],'runs':runs}
    with serve(assets,max_requests=policy['max_requests'],max_response_bytes=policy['max_response_bytes']) as server:
      try:
        with sync_playwright() as pw:
          browser=pw.chromium.launch(executable_path=config['chromium_executable'],headless=True,
             chromium_sandbox=not config['allow_unsandboxed_diagnostic'],
             args=['--disable-background-networking','--disable-extensions','--disable-sync'])
          try:
            result['browser_version']=browser.version
            for index in range(r['replay_count']):
              context=browser.new_context(viewport=r['viewport'],device_scale_factor=1,locale='en-US',
                  timezone_id='UTC',service_workers='block',accept_downloads=False,
                  reduced_motion='reduce',color_scheme='light')
              events={k:[] for k in ('blocked_requests','page_errors','console_errors','violations')}
              overflow=[False];responses=[];start=len(server.snapshot()['records']);readiness=[]
              def record(kind,value):
                if len(events[kind])>=limits.max_events:overflow[0]=True
                else:events[kind].append(str(value).replace(server.origin,'<local-origin>')[:1024])
              try:
                def route(req):
                  try:route_path(req.request.url,server.origin,req.request.method,assets)
                  except BenchmarkError:
                    record('blocked_requests',req.request.method+' '+req.request.url);req.abort();return
                  req.continue_()
                context.route('**/*',route)
                if not hasattr(context,'route_web_socket'):raise BenchmarkError('BROWSER_WEBSOCKET_CONTROL_UNAVAILABLE')
                def websocket(ws):record('blocked_requests','WEBSOCKET '+ws.url);ws.close()
                context.route_web_socket('**/*',websocket)
                context.on('page',lambda page:record('violations','UNEXPECTED_PAGE') if len(context.pages)>1 else None)
                page=context.new_page();page.set_default_timeout(limits.action_timeout_ms)
                page.on('pageerror',lambda err:record('page_errors',err))
                page.on('console',lambda msg:record('console_errors',msg.text) if msg.type=='error' else None)
                def dialog(d):record('violations','DIALOG');d.dismiss()
                page.on('dialog',dialog);page.on('download',lambda d:record('violations','DOWNLOAD'))
                def on_response(resp):
                  if len(responses)>=policy['max_requests']:overflow[0]=True
                  else:responses.append(resp)
                page.on('response',on_response)
                url=server.origin+'/'+c['entrypoint']
                readiness.append(navigate(page,url,policy['ready'],limits.action_timeout_ms))
                def reload():readiness.append(navigate(page,url,policy['ready'],limits.action_timeout_ms,reload=True))
                steps=run_steps(page,r['steps'],limits.action_timeout_ms,boot=reload)
                ax=collect_ax(page,policy['ax_checks']);wire=[];body_total=0
                for resp in list(responses):
                  name=route_path(resp.url,server.origin,resp.request.method,assets)
                  raw=resp.body();body_total+=len(raw)
                  if body_total>policy['max_response_bytes']:raise BenchmarkError('HTTP_RESPONSE_BYTE_LIMIT')
                  wire.append({'path':name,'method':resp.request.method,'status':resp.status,
                         'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'headers':resp.all_headers()})
                cdp=context.new_cdp_session(page)
                try:shot=base64.b64decode(cdp.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False})['data'],validate=True)
                finally:cdp.detach()
                if len(shot)>limits.max_screenshot_bytes:raise BenchmarkError('BROWSER_SCREENSHOT_LIMIT')
                if overflow[0] or server.snapshot()['limit_exceeded']:raise BenchmarkError('HTTP_EVENT_OR_RESOURCE_LIMIT')
                runs.append({'steps':steps,'events':events,'event_counts':{k:len(v) for k,v in events.items()},
                    'screenshot':{'sha256':hashlib.sha256(shot).hexdigest(),'size_bytes':len(shot),
                                  'png_base64':base64.b64encode(shot).decode()},'fresh_context_index':index,
                    'http_responses':wire,'http_server':server.snapshot()['records'][start:],
                    'readiness':readiness,'ax':ax})
              except BenchmarkError:
                result['partial_events']=events;raise
              finally:context.close()
          finally:browser.close()
        result['status']='COLLECTED'
      except BenchmarkError as exc:result['error_code']=exc.code
      except Exception as exc:
        result.update(error_code='HTTP_BROWSER_RUNTIME_EXCEPTION',exception_type=type(exc).__name__,diagnostic=str(exc)[:1200])
      result['server_accounting']=server.snapshot()
    return result

def main():
    try:
        raw=Path(sys.argv[1]).read_bytes()
        if len(raw)>1_000_000:raise BenchmarkError('BROWSER_CONFIG_LIMIT')
        result=collect(strict_loads(raw.decode('utf-8')))
    except Exception as exc:
        result={'status':'BLOCKED','error_code':exc.code if isinstance(exc,BenchmarkError) else 'HTTP_WORKER_EXCEPTION',
                'exception_type':type(exc).__name__}
    sys.stdout.write(canonical_json(result));return 0
if __name__=='__main__':raise SystemExit(main())
