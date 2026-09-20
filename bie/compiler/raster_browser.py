"""H8 real Chromium counterfactual pixel producer for diagnostic source fixtures.

Uses inherited explicit API-double TS bridge. Cannot mint an ActualPaintWitness.
Network is denied by routing; Chromium here is not an operational sandbox.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from hashlib import sha256
import json
import tempfile
from .qa_common import CompilerQAError, digest
from .render_process import run_bounded_process
from .host_toolchain import file_identity
from .raster_capture import build_raster_targets, capture_budget, frame_file, inspect_counterfactual_capture, DIAGNOSTIC_SCOPE

SUPPORT = Path(__file__).parent/'qa_support'


def measure_raster_scene(result, target, output: Path | str, *, browser: str = '/usr/bin/chromium') -> dict:
    from playwright.sync_api import sync_playwright
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise CompilerQAError('RASTER_DIAGNOSTIC_OUTPUT_EXISTS_OR_SYMLINK')
    if not result.receipt.source_gate_passed:
        raise CompilerQAError('RASTER_CHECKED_SOURCE_REQUIRED')
    raw = result.effective_document
    targets = build_raster_targets(raw)
    n = (raw['duration_ms'] * target.fps + 999)//1000
    capture_budget(target.width,target.height,n,len(targets))
    output.mkdir(parents=True)
    errors, network, frames, processes = [], [], [], []
    helper = (SUPPORT/'raster_modes.js').read_text()
    bridge = SUPPORT/('frame_runtime_bridge.cjs' if raw.get('metadata',{}).get('compiler_h6') is not None else 'layout_bridge.cjs')
    host = (SUPPORT/'layout_dom_host.js').read_text()
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=browser,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page = b.new_page(viewport={'width':target.width,'height':target.height},device_scale_factor=1)
        page.set_default_timeout(30000)
        page.route('**/*',lambda r:(network.append(r.request.url),r.abort())[-1])
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:white;color:black;font:16px sans-serif;}#root{width:100vw;height:100vh;}</style><div id="root"></div>')
        try:
            for start in range(0,n,32):
                req={'files':{f.path:f.content for f in result.codegen.files},'frames':list(range(start,min(n,start+32))),
                     'fps':target.fps,'width':target.width,'height':target.height}
                with tempfile.TemporaryDirectory() as td:
                    q=Path(td)/'request.json';q.write_text(json.dumps(req))
                    r=run_bounded_process(['node',str(bridge),str(q)],cwd=td,timeout_s=60,max_output_bytes=64*1024**2)
                processes.append({'process':asdict(r),'stdout_not_duplicated':True})
                # Large duplicate trees are omitted from the process receipt; the
                # original generated source and every actual PNG are retained.
                processes[-1]['process']['process']['stdout']='[generated tree output omitted; byte count/hash below]'
                processes[-1]['stdout_sha256']=sha256(r.process.stdout.encode()).hexdigest()
                if not r.process.passed:
                    raise CompilerQAError('RASTER_BRIDGE_FAILED:'+r.process.stderr[:500])
                data=json.loads(r.process.stdout)
                if data.get('execution_kind')!='REAL_TS_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES' or [x['frame'] for x in data['trees']]!=req['frames']:
                    raise CompilerQAError('RASTER_BRIDGE_IDENTITY')
                for tree in data['trees']:
                    f=tree['frame'];page.evaluate(host,tree['tree'])
                    page.wait_for_function("document.fonts.status === 'loaded'")
                    def shot(kind,index=None):
                        mode={'kind':'full'} if kind in {'full','repeat'} else {'kind':kind,'target_id':targets[index]['target_id']}
                        measured=page.evaluate(helper,{'targets':targets,'mode':mode,'frame':f})
                        if measured['fonts_ready'] is not True or measured['image_errors']:
                            raise CompilerQAError('RASTER_ASSETS_NOT_READY')
                        page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                        path=output/frame_file(f,kind,index)
                        page.screenshot(path=str(path),animations='allow')
                        return {'file':path.name,'sha256':file_identity(path)}, measured['inventory']
                    full,inventory=shot('full')
                    entries=[]
                    for i,spec in enumerate(targets):
                        row={'target_id':spec['target_id']}
                        for kind in ('baseline','isolated','muted'):
                            row[kind],observed=shot(kind,i)
                            if observed!=inventory:
                                raise CompilerQAError('RASTER_DOM_CHANGED_BETWEEN_MODES')
                        entries.append(row)
                    repeat,observed=shot('repeat')
                    if observed!=inventory:raise CompilerQAError('RASTER_DOM_NOT_RESTORED')
                    frames.append({'frame':f,'full':full,'repeat':repeat,'inventory':inventory,'targets':entries})
        finally:
            b.close()
    if network:errors.append('UNEXPECTED_NETWORK_REQUESTS_BLOCKED')
    capture={'schema_version':'bie.counterfactual-capture.v1','scope':DIAGNOSTIC_SCOPE,'scene_sha256':digest(raw),
             'manifest_sha256':result.codegen.manifest_sha256,'width':target.width,'height':target.height,'fps':target.fps,
             'frame_count':n,'targets':targets,'frames':frames,'browser_errors':errors}
    analysis=inspect_counterfactual_capture(output,capture,raw,target,result.codegen.manifest_sha256,expected_scope=DIAGNOSTIC_SCOPE)
    (output/'CAPTURE.json').write_text(json.dumps(capture,indent=2))
    (output/'ANALYSIS.json').write_text(json.dumps(analysis,indent=2))
    (output/'PRODUCER.json').write_text(json.dumps({'helper_sha256':file_identity(SUPPORT/'raster_modes.js'),'browser_sha256':file_identity(browser),
        'bridge_sha256':file_identity(bridge),'processes':processes,'network_denied':network,'browser_errors':errors,
        'real_react':False,'real_remotion':False,'browser_os_sandbox_enabled':False,'accepted':False},indent=2))
    return analysis
