"""H4-003: disposable Chromium worker. Not an OS/network hostile-code sandbox.
Only evaluator-owned config reaches this entrypoint; candidate files are served
from a private manifest snapshot under a virtual origin, with no server socket.
"""
from __future__ import annotations
import base64, hashlib, json, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
# The worker is invoked by absolute filename from a clean environment.
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import BenchmarkError, canonical_json, strict_loads
from bie.evaluation.benchmarks.browser.contracts import MIME, BrowserLimits, reference, candidate
from bie.evaluation.benchmarks.browser.actions import run_steps

ORIGIN='https://bie-eval.invalid'
CSP="default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; worker-src 'none'; frame-ancestors 'none'"

def collect(config):
    from playwright.sync_api import sync_playwright
    limits=BrowserLimits(**config['limits']).validate()
    ref=reference(config['reference'],limits=limits);cand=candidate(config['candidate'],limits)
    root=Path(config['snapshot_root']);assets={}
    for row in cand['files']:
        raw=(root/row['path']).read_bytes()
        if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise BenchmarkError('BROWSER_SNAPSHOT_CHANGED')
        assets[row['path']]=raw
    from bie.evaluation.benchmarks.browser.document import prepare
    shell,scripts,transport=prepare(cand,assets)
    runs=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=config['chromium_executable'],headless=True,
            chromium_sandbox=not config['allow_unsandboxed_diagnostic'],
            args=['--disable-background-networking','--disable-extensions','--disable-sync'])
        try:
            version=browser.version
            for replay_index in range(ref['replay_count']):
                context=browser.new_context(viewport=ref['viewport'],device_scale_factor=1,
                    locale='en-US',timezone_id='UTC',service_workers='block',accept_downloads=False,
                    reduced_motion='reduce',color_scheme='light')
                try:
                    events={'blocked_requests':[],'page_errors':[],'console_errors':[],'violations':[]}
                    event_counts={k:0 for k in events};overflow=[False]
                    def record(key,value):
                        event_counts[key]+=1
                        if len(events[key])<limits.max_events:events[key].append(str(value)[:1024])
                        else:overflow[0]=True
                    def handler(route):
                        record('blocked_requests',route.request.method+' '+route.request.url)
                        route.abort()
                    context.route('**/*',handler)
                    if not hasattr(context,'route_web_socket'):raise BenchmarkError('BROWSER_WEBSOCKET_CONTROL_UNAVAILABLE')
                    def websocket(ws):
                        record('blocked_requests','WEBSOCKET '+ws.url);ws.close()
                    context.route_web_socket('**/*',websocket)
                    context.on('page',lambda p: record('violations','UNEXPECTED_PAGE') if len(context.pages)>1 else None)
                    page=context.new_page();page.set_default_timeout(limits.action_timeout_ms)
                    page.on('pageerror',lambda err:record('page_errors',err))
                    page.on('console',lambda msg:record('console_errors',msg.text) if msg.type=='error' else None)
                    def dialog(d):record('violations','DIALOG');d.dismiss()
                    page.on('dialog',dialog)
                    page.on('download',lambda d:record('violations','DOWNLOAD'))
                    def boot():
                        # A new local document, not a URL reload. Network policy
                        # stays blocked; managed browser policy is not modified.
                        page.set_content(shell,wait_until='load',timeout=limits.action_timeout_ms)
                        for script in scripts:page.evaluate('(source) => { (0, eval)(source); }',script['code'])
                    boot()
                    steps=run_steps(page,ref['steps'],limits.action_timeout_ms,boot=boot)
                    if overflow[0]:raise BenchmarkError('BROWSER_EVENT_LIMIT')
                    # Native screenshot RPC avoids candidate-patched JS APIs
                    # used by high-level screenshot stabilization helpers.
                    cdp=context.new_cdp_session(page)
                    try:raw=base64.b64decode(cdp.send('Page.captureScreenshot',{'format':'png','fromSurface':True,'captureBeyondViewport':False})['data'],validate=True)
                    finally:cdp.detach()
                    if len(raw)>limits.max_screenshot_bytes:raise BenchmarkError('BROWSER_SCREENSHOT_LIMIT')
                    runs.append({'steps':steps,'events':events,'event_counts':event_counts,
                        'screenshot':{'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw),
                                      'png_base64':base64.b64encode(raw).decode('ascii')},
                        'fresh_context_index':replay_index})
                finally:context.close()
        finally:browser.close()
    return {'status':'COLLECTED','browser_version':version,'runs':runs,
            'network_mode':'ALL_PAGE_REQUESTS_ABORTED_NOT_OS_ISOLATION','transport':transport,
            'chromium_sandbox_requested':not config['allow_unsandboxed_diagnostic'],
            'hostile_code_sandbox_verified':False,'trusted_fixture_execution_only':True}

def main():
    try:
        raw=Path(sys.argv[1]).read_bytes()
        if len(raw)>1_000_000:raise BenchmarkError('BROWSER_CONFIG_LIMIT')
        result=collect(strict_loads(raw.decode('utf-8')))
    except Exception as exc:
        result={'status':'BLOCKED','error_code':exc.code if isinstance(exc,BenchmarkError) else 'BROWSER_WORKER_EXCEPTION',
                'exception_type':type(exc).__name__,'diagnostic':str(exc)[:1600]}
    sys.stdout.write(canonical_json(result));return 0
if __name__=='__main__':raise SystemExit(main())
