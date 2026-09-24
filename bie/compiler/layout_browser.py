"""H4 diagnostic evaluator: real Chromium, explicit React/Remotion doubles.

It executes only this repository's regenerated sources. This is not an OS
sandbox and its measurements cannot authorize a production media release.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
import tempfile
import time

from .content_fit_qa import BRIDGE_SCOPE
from .frame_layout import dimensions
from .host_toolchain import file_identity
from .qa_common import CompilerQAError, digest
from .render_process import run_bounded_process

SUPPORT = Path(__file__).parent/'qa_support'
MAX_FRAMES = 2400
MAX_LAYER_FRAMES = 12000
MAX_BROWSER_LAUNCH_ATTEMPTS = 2
BROWSER_LAUNCH_RETRY_DELAY_SECONDS = 0.25


class ChromiumLayoutProbe:
    """A controlled local probe; reports cannot be supplied to the repair CLI."""
    scope = BRIDGE_SCOPE

    def __init__(self, executable: str = '/usr/bin/chromium', *, timeout_ms: int = 30000):
        path = Path(executable)
        if not path.is_absolute() or not path.is_file():
            raise CompilerQAError('LAYOUT_BROWSER_UNAVAILABLE: explicit absolute executable required')
        if type(timeout_ms) is not int or not 1000 <= timeout_ms <= 120000:
            raise CompilerQAError('LAYOUT_BROWSER_TIMEOUT_INVALID')
        self.executable = str(path)
        self.timeout_ms = timeout_ms
        self.browser = None
        self.playwright = None

    def __enter__(self):
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
        self.browser = None
        for attempt in range(MAX_BROWSER_LAUNCH_ATTEMPTS):
            self.playwright = sync_playwright().start()
            try:
                self.browser = self.playwright.chromium.launch(executable_path=self.executable, headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage'], timeout=self.timeout_ms)
                return self
            except PlaywrightTimeoutError:
                self.playwright.stop(); self.playwright = None; self.browser = None
                if attempt + 1 < MAX_BROWSER_LAUNCH_ATTEMPTS:
                    time.sleep(BROWSER_LAUNCH_RETRY_DELAY_SECONDS)
                    continue
                raise
            except BaseException:
                self.playwright.stop(); self.playwright = None; self.browser = None
                raise
        raise RuntimeError('UNREACHABLE_BROWSER_LAUNCH_STATE')

    def __exit__(self, *args):
        try:
            if self.browser: self.browser.close()
        finally:
            if self.playwright: self.playwright.stop()

    def measure(self, result, target, output: Path, *, screenshots: bool = False, paint_checks: bool = False, asset_bytes=None) -> dict:
        if self.browser is None:
            raise CompilerQAError('LAYOUT_BROWSER_NOT_STARTED')
        if output.exists():
            raise CompilerQAError('LAYOUT_EVIDENCE_ALREADY_EXISTS')
        raw = result.effective_document
        n = dimensions(raw, target)
        if n > MAX_FRAMES or n*len(raw['elements']) > MAX_LAYER_FRAMES:
            raise CompilerQAError('LAYOUT_BROWSER_WORK_BUDGET: no sampled pass')
        output.mkdir(parents=True)
        has_media = raw.get('metadata',{}).get('compiler_media_v1') is not None
        if has_media and not asset_bytes:
            raise CompilerQAError('MEDIA_MEASUREMENT_BYTES_REQUIRED')
        bridge = SUPPORT/('frame_runtime_bridge.cjs' if raw.get('metadata',{}).get('compiler_h6') is not None else 'layout_bridge.cjs')
        if has_media: bridge=SUPPORT/'media_bridge.cjs'
        host = (SUPPORT/'layout_dom_host.js').read_text()
        measure_js = (SUPPORT/'layout_measure.js').read_text()
        errors = []; observations = []; screenshot_records = []; network = []; paint_records = []; media_records = []
        paint_js = (SUPPORT/'paint_measure.js').read_text() if paint_checks else None
        page = self.browser.new_page(viewport={'width':target.width,'height':target.height}, device_scale_factor=1)
        page.set_default_timeout(self.timeout_ms)
        from urllib.parse import urlsplit
        from hashlib import sha256
        if has_media:
            from .visual_assets import plan_visual_assets
            needed = {r['public_path']:r for r in plan_visual_assets(raw)['assets']}
            if set(asset_bytes) != set(needed): raise CompilerQAError('MEDIA_MEASUREMENT_ASSET_COVERAGE')
            for path,data in asset_bytes.items():
                if sha256(data).hexdigest()!=needed[path]['sha256']: raise CompilerQAError('MEDIA_MEASUREMENT_ASSET_HASH')
        else: needed={}
        def serve(route):
            url=urlsplit(route.request.url);relative=url.path.lstrip('/')
            if url.scheme=='https' and url.netloc=='bie-verified.invalid' and not url.query and relative in needed:
                data=asset_bytes[relative];headers={'Access-Control-Allow-Origin':'*','Accept-Ranges':'bytes'}
                content_range=route.request.headers.get('range');status=200
                if content_range:
                    import re
                    match=re.fullmatch(r'bytes=(\d+)-(\d*)',content_range)
                    if not match: route.abort();return
                    start=int(match[1]);end=int(match[2]) if match[2] else len(data)-1
                    if not 0<=start<=end<len(data): route.fulfill(status=416,body=b'');return
                    headers['Content-Range']=f'bytes {start}-{end}/{len(data)}';data=data[start:end+1];status=206
                route.fulfill(status=status,content_type=needed[relative]['media_type'],body=data,headers=headers)
            else: network.append(route.request.url);route.abort()
        page.route('**/*', serve)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content('<!doctype html><html><head><meta charset="utf-8"><base href="https://bie-verified.invalid/"><style>html,body{margin:0;background:white;color:black;font:16px sans-serif;}#root{width:100vw;height:100vh;}</style></head><body><div id="root"></div></body></html>')
        eq = {e['element_id']:e['props'].get('font_size',32) for e in raw['elements'] if e['element_type']=='equation'}
        tools = {'browser_executable_sha256':file_identity(self.executable), 'browser_version':self.browser.version,
                 'producer_source_sha256':file_identity(__file__),
                 'bridge_sha256':file_identity(bridge),
                 'dom_host_sha256':file_identity(SUPPORT/'layout_dom_host.js'),
                 'measurement_program_sha256':file_identity(SUPPORT/'layout_measure.js'),
                 'browser_os_sandbox_enabled':False,'network_request_policy':('EXACT_VERIFIED_MEMORY_ASSET_ALLOWLIST_NO_EXTERNAL_NETWORK' if has_media else 'ABORT_ALL'),
                 'real_react':False,'real_remotion':False, 'media_native_browser_diagnostic':has_media,'media_audio_played':False}
        process_receipts = []; fonts_ready = True
        try:
            for start in range(0,n,60):
                req={'files':{f.path:f.content for f in result.codegen.files}, 'frames':list(range(start,min(n,start+60))),
                     'fps':target.fps,'width':target.width,'height':target.height}
                with tempfile.TemporaryDirectory() as td:
                    path=Path(td)/'request.json';path.write_text(json.dumps(req))
                    child=run_bounded_process(['node',str(bridge),str(path)],cwd=td,timeout_s=60,max_output_bytes=64*1024*1024)
                process_receipts.append({'outcome':child.outcome,'passed':child.process.passed,'stdout_bytes':child.stdout_bytes,
                                         'stderr':child.process.stderr,'execution_kind':'EXPLICIT_API_DOUBLE_TS_BRIDGE'})
                if not child.process.passed:
                    raise CompilerQAError('LAYOUT_BRIDGE_FAILED: '+child.outcome+': '+child.process.stderr[:500])
                data=json.loads(child.process.stdout)
                if data.get('execution_kind')!='REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES':
                    raise CompilerQAError('LAYOUT_BRIDGE_SCOPE_MISMATCH')
                tools['typescript_parser_version']=data['typescript_version']
                if [t['frame'] for t in data['trees']] != req['frames']:
                    raise CompilerQAError('LAYOUT_BRIDGE_COVERAGE_MISMATCH')
                for item in data['trees']:
                    frame=item['frame'];page.evaluate(host,item['tree'])
                    if has_media:
                        page.evaluate("""async () => {
                          await Promise.all(Array.from(document.images).map(async im => {await im.decode();if(!im.naturalWidth)throw Error('MEDIA_IMAGE_DECODE_FAILED');}));
                          for (const v of document.querySelectorAll('video[data-bie-test-native-video]')) {
                            v.muted=true;
                            if(v.readyState<1) await new Promise((resolve,reject)=>{v.addEventListener('loadedmetadata',resolve,{once:true});v.addEventListener('error',()=>reject(Error('MEDIA_VIDEO_DECODE_FAILED')),{once:true});});
                            const at=Number(v.dataset.bieSourceTime);
                            if(!Number.isFinite(at)||at<0||at>=v.duration)throw Error('MEDIA_VIDEO_SEEK_RANGE');
                            if(Math.abs(v.currentTime-at)>1e-9||v.readyState<2) await new Promise((resolve,reject)=>{v.addEventListener('seeked',resolve,{once:true});v.addEventListener('error',()=>reject(Error('MEDIA_VIDEO_SEEK_FAILED')),{once:true});v.currentTime=at;});
                          }
                          await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
                        }""")
                    if has_media:
                        native = page.evaluate("""() => {
                          const records=[];
                          for (const im of document.images) records.push({kind:'image',width:im.naturalWidth,height:im.naturalHeight,complete:im.complete,source:new URL(im.src).pathname});
                          for (const v of document.querySelectorAll('video[data-bie-test-native-video]')) {
                            const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;
                            const ctx=c.getContext('2d');ctx.drawImage(v,0,0);const rgb=[];
                            // Bounded independent pixel samples away from the moving fixture marker.
                            for(const point of [[.1,.15],[.8,.15],[.1,.85],[.8,.85]]){
                              const x=Math.floor(v.videoWidth*point[0]),y=Math.floor(v.videoHeight*point[1]);
                              const px=ctx.getImageData(x,y,1,1).data;rgb.push({x,y,rgb:Array.from(px).slice(0,3)});
                            }
                            records.push({kind:'video',width:v.videoWidth,height:v.videoHeight,current_time:v.currentTime,requested_time:Number(v.dataset.bieSourceTime),ready_state:v.readyState,muted:v.muted,source:new URL(v.src).pathname,samples:rgb});
                          }
                          return records;
                        }""")
                        media_records.append({'frame':frame,'media':native})
                    page.wait_for_function("document.fonts.status === 'loaded'",timeout=self.timeout_ms)
                    fonts_ready = fonts_ready and page.evaluate("document.fonts.status === 'loaded'")
                    observations.extend(page.evaluate(measure_js,{'frame':frame,'equationFonts':eq}))
                    if paint_checks:paint_records.extend(page.evaluate(paint_js,{'frame':frame}))
                    if screenshots and frame in {0,n//2,n-1}:
                        name=f'frame-{frame:05d}.png';page.screenshot(path=str(output/name))
                        screenshot_records.append({'path':name,'sha256':file_identity(output/name),'frame':frame})
        finally:
            page.close()
            (output/'PROCESS_RECEIPTS.json').write_text(json.dumps(process_receipts,indent=2))
        report={'schema_version':'bie.h4-dom-observations.v1','scope':BRIDGE_SCOPE,
                'scene_identity':digest(raw),'manifest_sha256':result.codegen.manifest_sha256,
                'width':target.width,'height':target.height,'fps':target.fps,'frame_count':n,
                'fonts_ready':fonts_ready,'browser_errors':errors,'records':observations,
                'producer':tools,'blocked_network_requests':network,'screenshots':screenshot_records,
                'release_authorized':False,'accepted':False}
        if paint_checks:report['paint_records']=paint_records
        if has_media:report['native_media_observations']=media_records
        if network:
            report['browser_errors'].append('UNEXPECTED_NETWORK_REQUESTS_BLOCKED')
        (output/'MEASUREMENTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        return report
