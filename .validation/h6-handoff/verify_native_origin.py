"""GAME-AUD-009/024: strict native-origin proof of the actual packaged runtime.

No smoke-bundle injection, CSP weakening, unsandboxed browser, or production
acceptance inference is allowed. All failures are retained in the receipt.
"""
from pathlib import Path
from dataclasses import asdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import argparse, hashlib, json, os, platform, sys, traceback


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-root',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args(); source=args.source_root.resolve(); out=args.output.resolve()
    if out.exists(): raise SystemExit('Output must be fresh; failed attempts must not be overwritten')
    out.mkdir(parents=True); sys.path.insert(0,str(source))
    report={'schema_version':'bie.game.h6.native-origin/1','audit_ids':['GAME-AUD-009','GAME-AUD-024'],
            'checks':{},'passed':False,'product_accepted':False,'fixture_kind':'synthetic contract fixture; actual generated WAV tone',
            'page_errors':[],'console_errors':[],'served_sha256':{},'platform':platform.platform(),
            'workflow_commit':os.environ.get('GITHUB_SHA'),'workflow_run_id':os.environ.get('GITHUB_RUN_ID'),
            'verifier_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    server=None; thread=None
    def check(name,condition,detail=True):
        report['checks'][name]={'passed':bool(condition),'detail':detail}
        if not condition: raise AssertionError(name)
    try:
        from scripts.build_h6_browser_probe import probe_context
        from bie.game_engine.build_runtime_engine.workspace import build_workspace
        from bie.game_engine.build_runtime_engine.contracts import BuildPolicy
        from bie.game_engine.build_runtime_engine.sandbox import sandboxed_chromium,sandbox_evidence
        from bie.game_engine.react_runtime_engine.vendor import verify_vendor
        versions=verify_vendor()['versions']
        ctx,audio=probe_context(); ws=build_workspace(ctx,{'audio:probe':audio},out/'package')
        dist=ws.root/'dist'; expected={a.path:a.sha256 for a in ws.manifest.artifacts}
        headers=json.loads((dist/'runtime/security-headers.json').read_text())
        report['package_manifest']=asdict(ws.manifest)
        report['source_sha256']={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((source/'bie/game_engine').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self,*a,**kw): super().__init__(*a,directory=str(dist),**kw)
            def log_message(self,*a): pass
            def do_GET(self):
                if self.path=='/favicon.ico':
                    self.send_response(204);self.end_headers();return
                super().do_GET()
            def end_headers(self):
                for k,v in headers.items(): self.send_header(k,v)
                super().end_headers()
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        origin=f'http://127.0.0.1:{server.server_address[1]}'
        with sandboxed_chromium(BuildPolicy(),allow_loopback=True) as (browser,profile,worker):
            page=browser.new_page();page.set_viewport_size({'width':360,'height':740});page.emulate_media(reduced_motion='reduce')
            page.on('pageerror',lambda error:report['page_errors'].append(str(error)))
            page.on('console',lambda message:report['console_errors'].append(message.text) if message.type=='error' else None)
            responses=[]; page.on('response',lambda response:responses.append(response))
            browser.add_init_script("""globalThis.__probeTelemetry=[];globalThis.__BIE_GAME_TELEMETRY_CONFIG__={enabled:true,policy_id:'policy:probe',session_id:'session:probe:1'};globalThis.__BIE_GAME_TELEMETRY_SINK__=event=>__probeTelemetry.push(event);globalThis.__probeAudio={playing:0,ended:0,errors:[]};document.addEventListener('playing',()=>__probeAudio.playing++,true);document.addEventListener('ended',()=>__probeAudio.ended++,true);document.addEventListener('error',event=>{if(event.target instanceof HTMLMediaElement)__probeAudio.errors.push('media error');},true);""")
            response=page.goto(origin+'/runtime/index.html',wait_until='load',timeout=20000)
            page.wait_for_function('globalThis.__BIE_GAME_RUNTIME__?.booted === true',timeout=10000)
            check('actual_packaged_native_origin',response.status==200 and page.url==origin+'/runtime/index.html')
            check('unmodified_csp_header',response.headers.get('content-security-policy')==headers['Content-Security-Policy'])
            framework=page.evaluate('__BIE_GAME_RUNTIME__.framework')
            check('real_pinned_react',framework['reactVersion']==versions['react'] and framework['reactDomVersion']==versions['react-dom'] and framework['mountAPI']=='react-dom/client.createRoot',framework)
            app=page.locator('main[role="application"]');check('one_application',app.count()==1)
            check('rtl_locale',app.get_attribute('dir')=='rtl' and app.get_attribute('lang')=='ur-IN')
            check('mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            initial=page.evaluate('__BIE_GAME_RUNTIME__.getState()');button=page.locator('button[data-entity-id]').first
            button.focus();button.press('Enter')
            after=page.evaluate('({state:__BIE_GAME_RUNTIME__.getState(),score:__BIE_GAME_RUNTIME__.getScore(),events:__probeTelemetry})')
            check('native_keyboard_gameplay',initial['x']==1 and after['state']['x']==2 and after['score']==10,after)
            check('focus_retained',button.evaluate('(node)=>node===document.activeElement'))
            check('one_bound_telemetry_event',len(after['events'])==1 and after['events'][0]['session_id']=='session:probe:1')
            check('unknown_action_rejected',page.evaluate("()=>{try{__BIE_GAME_RUNTIME__.dispatch('unknown:action');return false}catch(e){return String(e.message).includes('ACTION_UNKNOWN')}}"))
            check('rejected_action_preserves_state',page.evaluate('__BIE_GAME_RUNTIME__.getState()')==after['state'])
            page.locator('[data-audio-control="play"]').click();page.wait_for_function('__probeAudio.ended>0',timeout=10000)
            audio_result=page.evaluate('__probeAudio');check('packaged_native_audio',audio_result['playing']>0 and not audio_result['errors'],audio_result)
            check('caption_cue_bound',page.locator('#bie-game-captions').get_attribute('data-cue-id')=='cue:narration:1')
            check('rights_visible','CC0-1.0' in page.locator('[data-rights-attribution]').inner_text())
            check('reduced_motion',page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches&&document.getAnimations().length===0"))
            shot=out/'runtime-react-mobile.png';page.screenshot(path=str(shot),full_page=True);report['screenshot_sha256']=hashlib.sha256(shot.read_bytes()).hexdigest()
            page.set_viewport_size({'width':768,'height':1024});check('tablet_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check('duplicate_mount_rejected',page.evaluate("async()=>{try{(await import('./entry.js')).startGameRuntime();return false}catch(e){return e.message==='GAME_REACT_ALREADY_MOUNTED'}}"))
            disposed=page.evaluate("()=>{const old=__BIE_GAME_RUNTIME__;old.dispose();old.dispose();let rejected=false;try{old.dispatch('drag:mover')}catch(e){rejected=e.message==='GAME_RUNTIME_DISPOSED'}return !old.booted&&rejected&&document.querySelectorAll('main[role=application]').length===0}")
            check('dispose_lifecycle',disposed)
            page.evaluate("async()=>{__BIE_GAME_TELEMETRY_CONFIG__.session_id='session:probe:2';(await import('./entry.js')).startGameRuntime()}")
            check('remount_initial_state',page.evaluate('__BIE_GAME_RUNTIME__.getState()')==initial)
            page.locator('button[data-entity-id]').first.press('Enter')
            check('deterministic_remount',page.evaluate('__BIE_GAME_RUNTIME__.getState()')==after['state'] and page.evaluate('__BIE_GAME_RUNTIME__.getScore()')==after['score'])
            report['sandbox']=asdict(sandbox_evidence(profile,worker));check('kernel_browser_isolation',True,report['sandbox'])
            for item in responses:
                if not item.url.startswith(origin+'/'): raise AssertionError('Unexpected response origin: '+item.url)
                relative=item.url[len(origin)+1:]
                if relative=='favicon.ico' and item.status==204: continue
                if item.status!=200: raise AssertionError('HTTP status: '+str(item.status)+' '+relative)
                digest=hashlib.sha256(item.body()).hexdigest()
                if expected.get(relative)!=digest: raise AssertionError('Served bytes differ from built manifest: '+relative)
                report['served_sha256'][relative]=digest
            check('native_module_graph_requested',all(p in report['served_sha256'] for p in ('runtime/index.html','runtime/entry.js','runtime/react-vendor.js','runtime/bootstrap.js')))
            check('actual_packaged_asset_requested',any(p.startswith('assets/') for p in report['served_sha256']))
            check('served_manifest_hashes_verified',True,len(report['served_sha256']))
            check('no_page_or_console_errors',not report['page_errors'] and not report['console_errors'])
            check('no_smoke_bundle_requested',not any('smoke-bundle' in p for p in report['served_sha256']))
            report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc()
    finally:
        if server: server.shutdown();server.server_close()
        if thread: thread.join(timeout=5)
        (out/'RESULT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','package_manifest')},indent=2,ensure_ascii=False))
    return 0 if report['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
