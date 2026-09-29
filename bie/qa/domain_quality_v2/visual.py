"""HARD017: native layout + actual static DOM/PNG correspondence.

The collector controls the browser; candidate script and requests are disabled.
This diagnostic set_content path is never represented as native Remotion/game.
Occlusion is sampled at five points, not certified for arbitrary paint/3D.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from io import BytesIO
import hashlib,math
from ...visual_intelligence.layout_contracts import LayoutPlan,make_layout_plan
from .common import *

@dataclass(frozen=True)
class VisualPolicy(PolicyDigest):
    viewport: tuple[int,int]
    required_ids: tuple[str,...]
    relationships: tuple[tuple[str,str,str],...]=()
    tolerance_millipixels: int=2000
    max_html_bytes: int=262144
    def __post_init__(self):
        require(type(self.viewport)is tuple and len(self.viewport)==2,'VIS_VIEWPORT')
        for v in self.viewport:integer(v,'viewport',100,2048)
        ids(self.required_ids,'VIS_NODE');require(type(self.relationships)is tuple and len(self.relationships)<=256,'VIS_RELATIONS')
        for a,r,b in self.relationships:require(a in self.required_ids and b in self.required_ids and r in ('left_of','above','separate'),'VIS_RELATION')
        integer(self.tolerance_millipixels,'tolerance',0,5000);integer(self.max_html_bytes,'html_limit',1,1048576)

def capture_html(html_ref,root,policy,*,browser='/usr/bin/chromium'):
    require(type(browser)is str and Path(browser).is_absolute(),'VIS_BROWSER_PATH')
    with SnapshotStore(root) as store:raw=store.read(html_ref)
    require(len(raw)<=policy.max_html_bytes,'VIS_HTML_LIMIT');html=raw.decode('utf-8',errors='strict')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=browser,headless=True,args=['--no-sandbox'])
        # Trusted authored diagnostic HTML only. --no-sandbox is explicit; this is
        # NOT the production hostile-document worker or a security certificate.
        try:
            ctx=b.new_context(viewport={'width':policy.viewport[0],'height':policy.viewport[1]},java_script_enabled=False,service_workers='block')
            blocked=[];ctx.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()))
            page=ctx.new_page();page.set_content(html,wait_until='load',timeout=15000)
            observed=page.evaluate("""() => {const nodes=[...document.querySelectorAll('[data-h4-id]')].map(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);let vis=s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0;let clipped=r.x<0||r.y<0||r.right>innerWidth||r.bottom>innerHeight;for(let a=n.parentElement;a;a=a.parentElement){let q=getComputedStyle(a),v=a.getBoundingClientRect();if(q.display==='none'||q.visibility!=='visible'||Number(q.opacity)===0)vis=false;if((q.overflowX!=='visible'&&(r.x<v.x||r.right>v.right))||(q.overflowY!=='visible'&&(r.y<v.y||r.bottom>v.bottom)))clipped=true;}const pts=[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]];const hits=pts.map(([x,y])=>{const h=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!h&&(h===n||n.contains(h));});return {id:n.dataset.h4Id,text:n.innerText,rect:[r.x,r.y,r.width,r.height],visible:vis,clipped:clipped,hit_samples:hits,unsupported:s.transform!=='none'||s.filter!=='none'||s.mixBlendMode!=='normal'||s.clipPath!=='none'||s.backgroundImage!=='none'};});return {nodes,active:document.querySelectorAll('script,iframe,object,embed,canvas,svg,img,video').length};}""")
            png=page.screenshot(type='png');version=b.version
        finally:b.close()
    return dict(schema_version='bie.qa.h4-static-capture/1',html_sha256=html_ref.sha256,viewport=list(policy.viewport),nodes=observed['nodes'],
        unsupported_markup=observed['active'],blocked_requests=blocked,browser_version=version,png_sha256=hashlib.sha256(png).hexdigest(),
        execution_mode='controlled_static_about_blank',native_runtime_verified=False,browser_sandbox_verified=False),png

def evaluate_visual(native,html_ref,source_refs,root,binding,policy,*,capture=None):
    require(type(native)is LayoutPlan,'VIS_NATIVE_LAYOUT')
    expected=make_layout_plan(evidence_refs=native.evidence_refs,reasoning_refs=native.reasoning_refs,nodes=native.nodes,constraints=native.constraints,warnings=native.warnings)
    require(native==expected,'VIS_EDITED_NATIVE_LAYOUT');require(binding.policy_digest==policy.content_digest,'H4_POLICY_BINDING')
    sources=verify_sources(root,source_refs);require(set(native.evidence_refs)<=set(sources),'VIS_SOURCE_BINDING')
    byid={n.node_id:n for n in native.nodes};require(set(byid)==set(policy.required_ids),'VIS_NATIVE_NODE_CENSUS')
    # A supplied observation may be inspected as evidence only; callers cannot use it
    # to obtain capture execution credit. Real capture is the default local path.
    supplied=capture is not None
    if supplied:obs,png=capture
    else:obs,png=capture_html(html_ref,root,policy)
    fields(obs,('schema_version','html_sha256','viewport','nodes','unsupported_markup','blocked_requests','browser_version','png_sha256','execution_mode','native_runtime_verified','browser_sandbox_verified'),'VIS_CAPTURE_FIELDS')
    require(obs['schema_version']=='bie.qa.h4-static-capture/1'and obs['html_sha256']==html_ref.sha256 and obs['viewport']==list(policy.viewport),'VIS_CAPTURE_BINDING')
    with SnapshotStore(root)as store:store.read(html_ref)
    require(type(png)is bytes and hashlib.sha256(png).hexdigest()==obs['png_sha256'],'VIS_PNG_HASH')
    from PIL import Image
    with Image.open(BytesIO(png))as im:require(im.format=='PNG'and im.size==policy.viewport,'VIS_PNG_DIMENSIONS');im.load()
    require(obs['execution_mode']=='controlled_static_about_blank'and obs['native_runtime_verified']is False and obs['browser_sandbox_verified']is False,'VIS_CAPTURE_SCOPE')
    integer(obs['unsupported_markup'],'unsupported_markup',0,100000);require(type(obs['blocked_requests'])is list and len(obs['blocked_requests'])<=10000 and all(type(x)is str for x in obs['blocked_requests']),'VIS_REQUEST_OBSERVATIONS');text(obs['browser_version'],'browser_version')
    findings=[];nodes=unique(items(obs['nodes'],'VIS_OBSERVATIONS',0,1024),'id','VIS_DUPLICATE_NODE')
    if set(nodes)!=set(byid):findings.append(Finding('RENDERED_CONTENT_INVENTORY_MISMATCH','layout','BLOCKER'))
    for nid,n in byid.items():
        if nid not in nodes:continue
        row=nodes[nid];fields(row,('id','text','rect','visible','clipped','hit_samples','unsupported'))
        require(type(row['rect'])is list and len(row['rect'])==4 and all(type(x)in(int,float)and math.isfinite(x)for x in row['rect']),'VIS_MEASURED_GEOMETRY')
        for flag in ('visible','clipped','unsupported'):require(type(row[flag])is bool,'VIS_OBSERVATION_FLAG')
        require(type(row['hit_samples'])is list and len(row['hit_samples'])==5 and all(type(x)is bool for x in row['hit_samples']),'VIS_HIT_SAMPLE_CENSUS')
        require(type(row['text'])is str,'VIS_DISPLAY_TEXT_TYPE')
        text(row['text'],'display_text') if row['text']else None
        if row['text']!=n.payload.get('text'):findings.append(Finding('RENDERED_TEXT_CHANGED',nid,'BLOCKER'))
        if not row['visible']or min(row['rect'][2:])<=0:findings.append(Finding('RENDERED_CONTENT_HIDDEN',nid,'BLOCKER'))
        if row['clipped']:findings.append(Finding('RENDERED_CONTENT_CROPPED',nid,'BLOCKER'))
        if not all(row['hit_samples']):findings.append(Finding('RENDERED_CONTENT_OCCLUDED',nid,'BLOCKER'))
        w,h=policy.viewport;wanted=(n.box.x*w,n.box.y*h,n.box.width*w,n.box.height*h)
        if any(abs(a-b)*1000>policy.tolerance_millipixels for a,b in zip(row['rect'],wanted)):findings.append(Finding('NATIVE_RENDER_LAYOUT_MISMATCH',nid,'BLOCKER'))
        if row['unsupported']:findings.append(Finding('COMPLEX_PAINT_REVIEW_REQUIRED',nid))
    for a,relation,b in policy.relationships:
        if a not in nodes or b not in nodes:continue
        x,y,w,h=nodes[a]['rect'];u,v,z,k=nodes[b]['rect']
        valid=x+w<=u if relation=='left_of'else y+h<=v if relation=='above'else(x+w<=u or u+z<=x or y+h<=v or v+k<=y)
        if not valid:findings.append(Finding('RENDERED_SCIENTIFIC_RELATION_CHANGED',a+':'+b,'BLOCKER'))
    if obs['unsupported_markup']or obs['blocked_requests']:findings.append(Finding('UNSUPPORTED_OR_EXTERNAL_CONTENT','layout'))
    findings.append(Finding('SUPPLIED_CAPTURE_REQUIRES_ATTESTATION'if supplied else 'STATIC_DIAGNOSTIC_NOT_NATIVE_RENDER','layout'))
    details=dict(capture=obs,native_layout_digest=native.fingerprint,actual_collector_executed=not supplied,full_occlusion_or_media_coverage=False)
    return (*finish('BIE-QA-HARD-017',binding,findings,(html_ref,*source_refs),details),png)
