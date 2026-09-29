"""Observe trusted, static, self-contained HTML in Chromium.

This is an opt-in diagnostic collector, NOT an untrusted-code sandbox. Caller must
use a separately isolated worker for hostile documents. Page JavaScript and all
network requests are disabled. Browser instrumentation evaluates fixed collector
code. Complex paint/stacking features are recorded as unsupported, never accepted
using a made-up average color. No font files or signing keys are exported.
"""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json, math
from ..release_v2.contracts import ArtifactRef,ContractError,canonical_bytes,token
from ..source_v2.io import SnapshotStore
from .models import Rect,RGBA,Measurement,VisualState,CaptureRef,ViewRequirement

# This JavaScript is fixed by the evaluator, not taken from the HTML candidate.
COLLECTOR = r'''() => {
 const unsupported = new Set();
 const all=[...document.querySelectorAll('*')];
 if(all.length>4096)throw Error('VIS_BROWSER_DOM_LIMIT');
 for(const e of all){let n=e,depth=0;while(n){if(++depth>64)throw Error('VIS_BROWSER_DEPTH_LIMIT');n=n.parentElement;}}
 const tracked = [...document.querySelectorAll('[data-vis-id]')];
 if (tracked.length > 256) throw Error('VIS_BROWSER_ELEMENT_LIMIT');
 const ids=tracked.map(e=>e.getAttribute('data-vis-id'));
 if(new Set(ids).size!==ids.length) throw Error('VIS_BROWSER_DUPLICATE_ID');
 if(document.querySelector('script,iframe,object,embed,video,audio,canvas,svg,math')) unsupported.add('active-or-complex-content');
 if(document.querySelector('link,base')) unsupported.add('external-or-base-reference');
 const box=r=>({x:r.x,y:r.y,width:r.width,height:r.height});
 const rgba=s=>{const m=s.match(/^rgba?\(([^)]+)\)$/); if(!m)return null;
   const v=m[1].split(/[ ,/]+/).filter(Boolean).map(Number);return v.length>=3?[v[0],v[1],v[2],v.length>3?v[3]:1]:null;};
 for(const e of all){
   if(e===document.documentElement||e===document.body||e.closest('[data-vis-id]')||['SCRIPT','STYLE','HEAD','META','TITLE'].includes(e.tagName))continue;
   const s=getComputedStyle(e),r=e.getBoundingClientRect(),c=rgba(s.backgroundColor);
   if(r.width>0&&r.height>0&&s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&
      (c&&c[3]>0||s.backgroundImage!=='none'||parseFloat(s.borderTopWidth)>0||['IMG','INPUT','BUTTON','CANVAS','SVG'].includes(e.tagName)))unsupported.add('untracked-visible-paint');
 }
 let textNodes=0;
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()){
   if(++textNodes>8192)throw Error('VIS_BROWSER_TEXT_NODE_LIMIT');
   const n=walker.currentNode,p=n.parentElement;
   if(!p||!n.textContent.trim()||p.closest('script,style'))continue;
   const s=getComputedStyle(p),r=p.getBoundingClientRect();
   if(s.display!=='none'&&s.visibility==='visible'&&r.width&&r.height&&!p.closest('[data-vis-id]')) unsupported.add('untracked-visible-text');
 }
 const measurements=tracked.map(e=>{
   const flags=new Set();const s=getComputedStyle(e),r=e.getBoundingClientRect();
   if(e.querySelector('[data-vis-id]')) flags.add('nested-tracked-elements');
   if(e.shadowRoot) flags.add('shadow-root');
   if(e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+1)flags.add('scroll-overflow');
   let clip={x:0,y:0,right:innerWidth,bottom:innerHeight},opacity=1,shown=true;
   let bg=null,known=true;
   for(let a=e;a;a=a.parentElement){
     const c=getComputedStyle(a),b=a.getBoundingClientRect();
     opacity*=Number(c.opacity);
     if(Number(c.opacity)<1){known=false;flags.add('group-opacity-compositing');}
     if(c.display==='none'||c.visibility!=='visible')shown=false;
     if(c.transform!=='none'||c.perspective!=='none')flags.add('transformed-geometry');
     if(c.filter!=='none'||c.backdropFilter&&c.backdropFilter!=='none')flags.add('filter');
     if(c.mixBlendMode!=='normal')flags.add('blend-mode');
     if(c.isolation==='isolate'||c.zIndex!=='auto')flags.add('complex-stacking');
     if(c.clipPath!=='none'||c.maskImage&&c.maskImage!=='none')flags.add('complex-clip-or-mask');
     if(c.animationName!=='none'||c.transitionDuration.split(',').some(x=>parseFloat(x)>0))flags.add('time-varying-style');
     if(c.backgroundImage!=='none'){known=false;flags.add('nonuniform-background');}
     if(c.boxShadow!=='none'||c.textShadow!=='none')flags.add('shadow-paint');
     if(c.textTransform!=='none')flags.add('transformed-text');
     if(c.writingMode!=='horizontal-tb')flags.add('vertical-text');
     for(const pseudo of ['::before','::after']){const ps=getComputedStyle(a,pseudo);if(ps.content!=='none'&&ps.content!=='normal'&&ps.content!=='""') flags.add('generated-content');}
     if(!bg){const color=rgba(c.backgroundColor);if(color&&color[3]===1)bg=color;else if(color&&color[3]>0){known=false;flags.add('translucent-background');}}
     if(a!==e){
       if(['hidden','clip','scroll','auto'].includes(c.overflowX)){clip.x=Math.max(clip.x,b.x);clip.right=Math.min(clip.right,b.right);}
       if(['hidden','clip','scroll','auto'].includes(c.overflowY)){clip.y=Math.max(clip.y,b.y);clip.bottom=Math.min(clip.bottom,b.bottom);}
     }
   }
   if(!bg){bg=[255,255,255,1];known=false;flags.add('unknown-canvas-background');}
   for(const px of [0.2,0.5,0.8])for(const py of [0.2,0.5,0.8]){
     const xx=r.x+r.width*px,yy=r.y+r.height*py;
     if(xx>=0&&yy>=0&&xx<innerWidth&&yy<innerHeight){const top=document.elementFromPoint(xx,yy);if(top&&top!==e&&!e.contains(top))flags.add('sampled-occlusion-or-hit-test-ambiguity');}
   }
   const foreground=rgba(s.color)||[0,0,0,1];
   const lines=[];const tw=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let count=0;
   while(tw.nextNode()){
     const n=tw.currentNode;if(!n.textContent.length)continue;
     if(++count>512)throw Error('VIS_BROWSER_LINE_LIMIT');
     const ns=getComputedStyle(n.parentElement);
     if(ns.font!==s.font||ns.color!==s.color)flags.add('mixed-text-style');
     const range=document.createRange();range.selectNodeContents(n);
     for(const rr of range.getClientRects())if(rr.width>0&&rr.height>0){lines.push(box(rr));if(lines.length>512)throw Error('VIS_BROWSER_LINE_LIMIT');}
   }
   return {object_id:e.getAttribute('data-vis-id'),box:box(r),clip:{x:clip.x,y:clip.y,width:Math.max(0,clip.right-clip.x),height:Math.max(0,clip.bottom-clip.y)},
    text:e.innerText||'',font_px:parseFloat(s.fontSize),foreground,background:bg,opacity,
    displayed:shown&&r.width>0&&r.height>0,background_known:known,fonts_loaded:document.fonts.status==='loaded',line_boxes:lines,unsupported:[...flags].sort()};
 });
 return {measurements,unsupported:[...unsupported].sort()};
}'''


def _rect(d):
    # Millipixel rounding error <= 0.5 unit, covered by the operator's explicit
    # tolerance. Zero extents are marked hidden and represented by a 1-unit box.
    return Rect(round(d['x']*1000),round(d['y']*1000),max(1,round(d['width']*1000)),max(1,round(d['height']*1000)))


def _color(a):
    return RGBA(*(max(0,min(255,round(x))) for x in a[:3]),max(0,min(255,round(a[3]*255))))


def measurement_from_browser(d):
    return Measurement(d['object_id'],_rect(d['box']),_rect(d['clip']),d['text'],round(d['font_px']*1000),
        _color(d['foreground']),_color(d['background']),max(0,min(1000000,round(d['opacity']*1000000))),
        d['displayed'] and d['clip']['width']>0 and d['clip']['height']>0,d['background_known'],d['fonts_loaded'],
        tuple(_rect(r) for r in d['line_boxes']),tuple(d['unsupported']))


def capture_static_html(artifact_root,html,view,*,capture_id,state_id,scene_id,start_ms,end_ms,output_dir,executable_path='/usr/bin/chromium',timeout_ms=15000):
    """Return a sampled VisualState and unsigned CaptureRef; output_dir must be new.

    HTML is caller-reviewed trusted static markup. External requests and page JS
    are disabled, but this helper is not a substitute for OS isolation.
    """
    if type(html) is not ArtifactRef or html.role!='support' or type(view) is not ViewRequirement:
        raise ContractError('VIS_BROWSER_INPUT_TYPE')
    from ..release_v2.contracts import integer
    integer(timeout_ms,'timeout_ms',100,60000)
    for v in (capture_id,state_id,scene_id):token(v,'capture identity')
    for suffix in ('-measurements','-screenshot'):token(capture_id+suffix,'capture artifact identity')
    unresolved_root=Path(artifact_root)
    root=unresolved_root.resolve();out=Path(output_dir)
    if not out.is_absolute():out=root/out
    if not out.resolve().is_relative_to(root):raise ContractError('VIS_BROWSER_OUTPUT_ESCAPE')
    if any(p.is_symlink() for p in (out,*out.parents)):raise ContractError('VIS_BROWSER_OUTPUT_SYMLINK')
    if out.exists():raise ContractError('VIS_BROWSER_OUTPUT_EXISTS')
    with SnapshotStore(unresolved_root) as store:raw=store.read(html)
    if len(raw)>2*1024*1024:raise ContractError('VIS_BROWSER_HTML_LIMIT')
    try:markup=raw.decode('utf-8')
    except UnicodeDecodeError as exc:raise ContractError('VIS_BROWSER_HTML_UTF8') from exc
    # Caller-reviewed HTML only; record script/complex content as unsupported.
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=executable_path,headless=True,args=['--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':view.width_px,'height':view.height_px},device_scale_factor=1,
                java_script_enabled=False,service_workers='block',locale='en-US',color_scheme='light',reduced_motion='reduce')
            context.route('**/*',lambda route:route.abort())
            page=context.new_page();page.set_default_timeout(timeout_ms)
            page.set_content(markup,wait_until='load',timeout=timeout_ms)
            page.evaluate('() => document.fonts.ready.then(() => true)')
            observed=page.evaluate(COLLECTOR)
            screenshot=page.screenshot(type='png',full_page=False,animations='disabled',timeout=timeout_ms)
            version=browser.version
            context.close();browser.close()
    except ImportError as exc:raise ContractError('VIS_BROWSER_UNAVAILABLE') from exc
    except Exception as exc:
        if isinstance(exc,ContractError):raise
        raise ContractError('VIS_BROWSER_CAPTURE_FAILED') from exc
    state=VisualState(state_id,scene_id,view.view_id,start_ms,end_ms,tuple(measurement_from_browser(m) for m in observed['measurements']),'sampled',capture_id)
    payload={'schema_version':'1.0.0','html_sha256':html.sha256,'screenshot_sha256':sha256(screenshot).hexdigest(),
             'viewport':[view.width_px,view.height_px],'state':asdict(state),'renderer_id':'chromium-static','renderer_version':version,
             'mode':'static-html-sample','unsupported':observed['unsupported']}
    data=canonical_bytes(payload);out.mkdir(parents=True,exist_ok=False)
    png_path=out/'frame.png';json_path=out/'measurements.json'
    png_path.write_bytes(screenshot);json_path.write_bytes(data)
    def ref(path,blob,aid,role):return ArtifactRef(aid,path.relative_to(root).as_posix(),sha256(blob).hexdigest(),len(blob),role)
    cap=CaptureRef(capture_id,state_id,html,ref(json_path,data,capture_id+'-measurements','support'),ref(png_path,screenshot,capture_id+'-screenshot','support'),'chromium-static',version)
    return state,cap
