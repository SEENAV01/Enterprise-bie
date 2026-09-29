"""Explicit trusted-fixture HTTP entrypoint collector; never invoked by evaluate.

Serves an immutable in-memory byte snapshot of declared outputs on loopback. Uses
real locator input, not a game's dispatch() or a DevTools-injected replacement
bundle. Not a hostile-code sandbox. Disabled without explicit diagnostic opt-in.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
import threading,time,hashlib,mimetypes
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,integer,revision,token,safe_relative_path
from ..source_v2.io import SnapshotStore
from .models import GamePolicy,RuntimeReceipt,Trace,Step,ObservedValue,LoadedAsset,inventory,refs

def collect(outputs,build_receipt,policy,root,*,run_id,code_revision,issued_at,output_prefix='game_capture',chromium='/usr/bin/chromium',allow_trusted_diagnostic=False,diagnostic_inline=False):
    if type(diagnostic_inline) is not bool:raise ContractError('GAME_CAPTURE_MODE')
    if allow_trusted_diagnostic is not True:raise ContractError('GAME_CAPTURE_REQUIRES_TRUSTED_DIAGNOSTIC_OPT_IN')
    if type(policy) is not GamePolicy or type(build_receipt) is not ArtifactRef:raise ContractError('GAME_CAPTURE_TYPE')
    token(run_id,'run_id');revision(code_revision);integer(issued_at,'issued_at');refs(outputs,'outputs');safe_relative_path(output_prefix)
    if sum((len(c.action_ids)+1)*policy.replays for c in policy.scenarios)>256:raise ContractError('GAME_CAPTURE_STEP_BUDGET')
    if not Path(chromium).is_absolute():raise ContractError('GAME_BROWSER_OPERATOR_PATH')
    root=Path(root);dest=root/output_prefix
    # Output path must be new and rooted in an existing operator-owned directory.
    if dest.exists():raise ContractError('GAME_CAPTURE_OUTPUT_EXISTS')
    if not root.is_dir() or root.is_symlink() or any((root/Path(*Path(output_prefix).parts[:i])).is_symlink() for i in range(1,len(Path(output_prefix).parts)+1)):raise ContractError('GAME_CAPTURE_OUTPUT_ROOT')
    with SnapshotStore(root) as store:payload={a.path:store.read(a) for a in outputs};store.read(build_receipt)
    if policy.entrypoint not in payload:raise ContractError('GAME_CAPTURE_ENTRYPOINT')
    dest.mkdir(parents=True,exist_ok=False)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parts=urlsplit(self.path);path=parts.path.lstrip('/')
            if parts.query or parts.fragment or path not in payload:self.send_error(404);return
            b=payload[path];self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(path)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
        def log_message(self,*a):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();origin=f'http://127.0.0.1:{server.server_address[1]}'
    traces=[];loaded={};page_errors=[];console_errors=[];violations=[];screen_refs=[]
    def record(arr,msg):
        if len(arr)<256:arr.append(str(msg)[:4096])
        else:raise ContractError('GAME_CAPTURE_EVENT_BUDGET')
    def write(path,data,aid):
        target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
        return ArtifactRef(aid,path,hashlib.sha256(data).hexdigest(),len(data),'support')
    try:
        from playwright.sync_api import sync_playwright,Error as PlaywrightError
        with sync_playwright() as pw:
            # Root CI lacks sandbox prerequisites. Explicitly labelled unverified;
            # production must use the separately governed isolated browser worker.
            browser=pw.chromium.launch(executable_path=chromium,headless=True,chromium_sandbox=False,args=['--disable-dev-shm-usage'])
            version=browser.version;actions={a.action_id:a for a in policy.actions}
            for c in policy.scenarios:
                for replay in range(policy.replays):
                    ctx=browser.new_context(viewport=dict(width=c.width,height=c.height),service_workers='block',accept_downloads=False)
                    trace_loaded=set()
                    def route(rt):
                        req=rt.request;u=urlsplit(req.url);path=u.path.lstrip('/')
                        if req.url.startswith(origin+'/') and not u.query and not u.fragment and req.method=='GET' and path in payload:rt.continue_()
                        else:record(violations,'unapproved-request:'+u.scheme+'://'+u.netloc+u.path[:512]);rt.abort()
                    ctx.route('**/*',route)
                    ctx.route_web_socket('**/*',lambda ws:(record(violations,'websocket-attempt'),ws.close()))
                    page=ctx.new_page();page.set_default_timeout(min(policy.max_action_ms,1500))
                    page.on('pageerror',lambda e:record(page_errors,e));page.on('console',lambda m:record(console_errors,m.text) if m.type=='error' else None)
                    page.on('popup',lambda p:(record(violations,'popup-attempt'),p.close()))
                    page.on('download',lambda d:(record(violations,'download-attempt'),d.cancel()))
                    page.on('worker',lambda w:record(violations,'worker-attempt'))
                    def response(resp):
                        u=urlsplit(resp.url);path=u.path.lstrip('/')
                        if resp.url.startswith(origin+'/') and path in payload:
                            if resp.status!=200:record(page_errors,'asset-http-status:'+str(resp.status));return
                            b=resp.body();loaded[path]=LoadedAsset(path,hashlib.sha256(b).hexdigest(),len(b));trace_loaded.add(path)
                    page.on('response',response);steps=[];clock=time.monotonic()
                    def navigate():
                        if not diagnostic_inline:
                            page.goto(origin+'/'+policy.entrypoint,wait_until='networkidle',timeout=policy.max_action_ms)
                            return
                        # Explicit offline DOM diagnostic only, never network/native evidence.
                        # Input JavaScript is the actual compiler output, in a private lexical
                        # wrapper. This supports only one simple external module, no imports.
                        import re,posixpath
                        html=payload[policy.entrypoint].decode('utf-8')
                        pattern=r'<script type="module" src="([^"<>]+)"></script>'
                        matches=re.findall(pattern,html)
                        if len(matches)!=1 or html.count('<script')!=1:raise ContractError('GAME_INLINE_SINGLE_MODULE_REQUIRED')
                        script_path=posixpath.normpath(posixpath.join(posixpath.dirname(policy.entrypoint),matches[0]))
                        page.set_content(re.sub(pattern,'',html),wait_until='load')
                        if script_path in payload:
                            js=payload[script_path].decode('utf-8')
                            if re.search(r'\b(?:import|export)\b',js):raise ContractError('GAME_INLINE_MODULE_IMPORT_UNSUPPORTED')
                            page.add_script_tag(content='(()=>{'+js+'\n})();')
                    for i,aid in enumerate(('boot',)+c.action_ids):
                        start=int((time.monotonic()-clock)*1000);error='';ok=True
                        try:
                            if aid=='boot':navigate()
                            else:
                                a=actions[aid];loc=page.locator(a.selector) if a.selector else None
                                if a.kind=='click':loc.click()
                                elif a.kind=='press':loc.press(a.value)
                                elif a.kind=='fill':loc.fill(a.value)
                                elif a.kind=='drag':loc.drag_to(page.locator(a.value))
                                elif a.kind=='reload':navigate() if diagnostic_inline else page.reload(wait_until='networkidle',timeout=policy.max_action_ms)
                            page.wait_for_timeout(50) # fixed observation delay, never wait for oracle answer
                        except PlaywrightError as e:ok=False;error=type(e).__name__+':'+str(e)[:1000]
                        if page.url!=('about:blank' if diagnostic_inline else origin+'/'+policy.entrypoint):record(violations,'unexpected-navigation')
                        vals=[]
                        for o in policy.observables:
                            loc=page.locator(o.selector);n=loc.count();visible=n==1 and loc.is_visible();v=loc.inner_text().strip() if n==1 else ''
                            vals.append(ObservedValue(o.key,v,n,visible))
                        image=page.screenshot(type='png',full_page=False);aid_image=f'{c.scenario_id}-{replay}-{i}';ref=write(f'{output_prefix}/{aid_image}.png',image,'capture-'+aid_image);screen_refs.append(ref)
                        end=int((time.monotonic()-clock)*1000);steps.append(Step(aid,start,end,ok,error,tuple(vals),ref))
                    traces.append(Trace(c.scenario_id,replay,c.width,c.height,tuple(steps),tuple(sorted(trace_loaded))));ctx.close()
            browser.close()
        receipt=RuntimeReceipt('bie.qa.game-runtime/1',run_id,code_revision,policy.game_id,build_receipt.sha256,inventory(outputs),policy.oracle_digest,policy.entrypoint,'about:blank' if diagnostic_inline else origin,'injected_bundle' if diagnostic_inline else 'http_entrypoint',version,issued_at,'authored_diagnostic',False,tuple(loaded[p] for p in sorted(loaded)),tuple(traces),tuple(page_errors),tuple(console_errors),tuple(violations))
        ref=write(f'{output_prefix}/runtime.json',canonical_bytes(asdict(receipt)),'captured-runtime')
        return ref,receipt,tuple(screen_refs)
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
