from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from urllib.request import urlopen
from contextlib import contextmanager
import base64, json, re, hashlib
from .errors import GameBuildError
from .sandbox import sandboxed_chromium,sandbox_evidence
from .contracts import BuildPolicy
from .module_graph import verify_module_graph

_IMPORT=re.compile(r'(from\s+["\'])(\./[^"\']+)(["\'])')
@dataclass(frozen=True)
class DeploymentEvidence:
    static_origin_verified:bool
    native_esm_loader_verified:bool
    exact_module_count:int
    module_graph_fingerprint:str
    entry_source_sha256:str
    browser_origin_navigation_verified:bool
    origin_block_reason:str|None
    sandbox_evidence:object
    product_accepted:bool=False
    def validate(self):
        if not self.static_origin_verified or not self.native_esm_loader_verified or self.exact_module_count<2:raise GameBuildError('GAME_BUILD_DEPLOYMENT_EVIDENCE')
        if not self.module_graph_fingerprint.startswith('sha256:') or len(self.entry_source_sha256)!=64 or self.product_accepted:raise GameBuildError('GAME_BUILD_DEPLOYMENT_EVIDENCE_SCOPE')
        return self

class _Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,directory=None,headers=None,**kw):self._bie_headers=headers or {};super().__init__(*a,directory=directory,**kw)
    def end_headers(self):
        for k,v in self._bie_headers.items():self.send_header(k,v)
        super().end_headers()
    def log_message(self,fmt,*args):pass

@contextmanager
def _origin(runtime:Path):
    headers=json.loads((runtime/'security-headers.json').read_text())
    def factory(*a,**kw):return _Handler(*a,directory=str(runtime),headers=headers,**kw)
    server=ThreadingHTTPServer(('127.0.0.1',0),factory);thread=Thread(target=server.serve_forever,daemon=True);thread.start();port=server.server_address[1]
    try:yield port,headers
    finally:server.shutdown();server.server_close();thread.join(timeout=2)

def _static_probe(port):
    with urlopen(f'http://127.0.0.1:{port}/index.html',timeout=3) as r:
        html=r.read();csp=r.headers.get('Content-Security-Policy','')
        if r.status!=200 or b'entry.js' not in html or "frame-ancestors 'none'" not in csp:raise GameBuildError('GAME_BUILD_STATIC_ORIGIN_INDEX')
    with urlopen(f'http://127.0.0.1:{port}/entry.js',timeout=3) as r:
        if r.status!=200 or 'javascript' not in (r.headers.get('Content-Type','')):raise GameBuildError('GAME_BUILD_STATIC_ORIGIN_MODULE_MIME')
    return True

def _data_graph(runtime:Path):
    graph=verify_module_graph(runtime);cache={};active=set()
    def convert(name):
        if name in cache:return cache[name]
        if name in active:raise GameBuildError('GAME_BUILD_NATIVE_ESM_CYCLE',name)
        active.add(name);p=runtime/name
        if not p.is_file():raise GameBuildError('GAME_BUILD_NATIVE_ESM_MODULE_MISSING',name)
        src=p.read_text()
        def repl(m):return m.group(1)+convert(m.group(2)[2:])+m.group(3)
        out=_IMPORT.sub(repl,src);active.remove(name)
        url='data:text/javascript;base64,'+base64.b64encode(out.encode()).decode();cache[name]=url;return url
    entry=convert('entry.js');return graph,entry,hashlib.sha256((runtime/'entry.js').read_bytes()).hexdigest(),cache

def deployment_smoke(dist,policy=BuildPolicy()):
    policy.validate();runtime=Path(dist)/'runtime';graph,entry_url,entry_sha,cache=_data_graph(runtime);blocked=None;origin_ok=False;sb=None
    with _origin(runtime) as (port,headers):
        static_ok=_static_probe(port)
        with sandboxed_chromium(policy,allow_loopback=True) as (ctx,profile,manifest):
            page=ctx.pages[0] if ctx.pages else ctx.new_page();errors=[];page.on('console',lambda msg: errors.append(msg.text) if msg.type=='error' else None);page.on('pageerror',lambda err:errors.append(str(err)))
            shell='<!doctype html><html><body><div id="bie-game-root"></div><script type="module" src="'+entry_url+'"></script></body></html>'
            page.set_content(shell,wait_until='load',timeout=policy.browser_timeout_ms);page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted === true',timeout=policy.browser_timeout_ms)
            if errors:raise GameBuildError('GAME_BUILD_NATIVE_ESM_ERRORS',' | '.join(errors)[:1000])
            if page.locator('main[role="application"]').count()!=1:raise GameBuildError('GAME_BUILD_NATIVE_ESM_APPLICATION_ROOT')
            sb=sandbox_evidence(profile,manifest)
            try:
                page.goto(f'http://127.0.0.1:{port}/index.html',wait_until='load',timeout=3000);page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted === true',timeout=3000);origin_ok=True
            except Exception as e:
                msg=str(e);blocked='ERR_BLOCKED_BY_ADMINISTRATOR' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in msg else ('ERR_BLOCKED_BY_CLIENT' if 'ERR_BLOCKED_BY_CLIENT' in msg else 'ORIGIN_NAVIGATION_BLOCKED')
    return DeploymentEvidence(static_ok,True,len(cache),graph['graph_fingerprint'],entry_sha,origin_ok,blocked,sb,False).validate()
