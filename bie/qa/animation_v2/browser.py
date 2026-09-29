"""Optional trusted-HTML diagnostic collector using paused CSS animation clocks.

Never load hostile documents here. Production requires an isolated worker,
network sandbox, attestation and resource quotas outside this process. The browser
is NOT a scientific truth evaluator. Its PNGs and measurements are sample evidence.
"""
from pathlib import Path
import hashlib
from .models import AnimationRequest,AnimationPolicy,CaptureRef
from .metrics import frame_time_ms
from ..release_v2.contracts import ArtifactRef,ContractError,token,canonical_bytes,safe_relative_path
from ..source_v2.io import SnapshotStore

INSPECT = r'''async ({time,expected}) => {
  const notes = new Set();
  if(document.querySelector('script,iframe,object,embed,canvas,video,audio,svg')) notes.add('UNSUPPORTED_ACTIVE_OR_COMPLEX_CONTENT');
  if(document.querySelector('link,base,img')) notes.add('UNSUPPORTED_EXTERNAL_OR_ASSET_CONTENT');
  const anims = document.getAnimations();
  if(anims.length>256) throw new Error('animation count bound');
  for(const a of anims) {a.pause();a.currentTime=time;}
  await Promise.all(anims.map(a=>a.ready));
  for(const a of anims) {
    const target=a.effect && a.effect.target;
    if(!target || !target.hasAttribute('data-bie-object')) notes.add('UNTRACKED_ANIMATION_TARGET');
    const tm=a.effect.getTiming();
    if(!Number.isFinite(tm.iterations) || tm.iterations!==1 || tm.direction!=='normal') notes.add('UNSUPPORTED_REPEAT_OR_DIRECTION');
  }
  const objects=[];
  for(const el of document.querySelectorAll('[data-bie-object]')) {
    const r=el.getBoundingClientRect(),s=getComputedStyle(el);
    let displayed=s.display!=='none' && s.visibility!=='hidden' && s.visibility!=='collapse';
    let opacity=Number(s.opacity);
    if(s.transform!=='none' || s.filter!=='none' || s.clipPath!=='none' || s.mixBlendMode!=='normal') notes.add('UNSUPPORTED_PAINT_OR_TRANSFORM');
    for(let p=el.parentElement;p;p=p.parentElement){
      const ps=getComputedStyle(p);displayed=displayed&&ps.display!=='none'&&ps.visibility!=='hidden';
      opacity*=Number(ps.opacity);
      if(ps.transform!=='none' || ps.filter!=='none' || ps.overflow==='hidden') notes.add('UNSUPPORTED_ANCESTOR_COMPOSITION');
    }
    objects.push({object_id:el.getAttribute('data-bie-object'),x_mpx:Math.round(r.x*1000),y_mpx:Math.round(r.y*1000),
      width_mpx:Math.round(r.width*1000),height_mpx:Math.round(r.height*1000),opacity_ppm:Math.round(opacity*1000000),displayed});
  }
  for(const el of document.querySelectorAll('body *')) {
    if(['STYLE','SCRIPT'].includes(el.tagName))continue;
    if(!el.closest('[data-bie-object]')) {
      const s=getComputedStyle(el),r=el.getBoundingClientRect();
      if(s.display!=='none'&&r.width>0&&r.height>0)notes.add('UNTRACKED_VISIBLE_CONTENT');
    }
    for(const ps of ['::before','::after'])if(!['none','normal','""'].includes(getComputedStyle(el,ps).content))notes.add('UNTRACKED_PSEUDO_CONTENT');
  }
  return {objects,unsupported:Array.from(notes).sort()};
}'''

def collect(request,policy,artifact_root,html_ref,mode_id,*,capture_id='browser-animation',executable_path='/usr/bin/chromium'):
    if type(request) is not AnimationRequest or type(policy) is not AnimationPolicy or type(html_ref) is not ArtifactRef:raise ContractError('ANI_COLLECTOR_TYPES')
    token(capture_id,'capture_id');safe_relative_path('animation_captures/'+capture_id+'-observations.json')
    if html_ref.role!='support':raise ContractError('ANI_CAPTURE_ROLE')
    modes={m.mode_id:m for m in policy.modes};requirements={x.mode_id:x for x in policy.captures}
    if mode_id not in modes or mode_id not in requirements:raise ContractError('ANI_COLLECTOR_MODE')
    m=modes[mode_id];spec=requirements[mode_id];root=Path(artifact_root)
    if m.width_px*m.height_px>16_777_216 or m.width_px*m.height_px*len(spec.frame_indices)>268_435_456:raise ContractError('ANI_COLLECTOR_PIXEL_BUDGET')
    with SnapshotStore(root) as store:html=store.read(html_ref)
    if len(html)>1024*1024:raise ContractError('ANI_COLLECTOR_HTML_LIMIT')
    try:text=html.decode('utf-8','strict')
    except UnicodeError as exc:raise ContractError('ANI_COLLECTOR_ENCODING') from exc
    base=root/'animation_captures'
    if base.is_symlink() or (base.exists() and not base.is_dir()):raise ContractError('ANI_COLLECTOR_OUTPUT_DIRECTORY')
    base.mkdir(exist_ok=True)
    target=base/capture_id
    target.mkdir(exist_ok=False)
    def save(name,data,aid):
        path=target/name
        with path.open('xb') as f:f.write(data)
        return ArtifactRef(aid,path.relative_to(root).as_posix(),hashlib.sha256(data).hexdigest(),len(data),'support')
    try:from playwright.sync_api import sync_playwright
    except ImportError as exc:raise ContractError('ANI_BROWSER_DEPENDENCY_UNAVAILABLE') from exc
    rows=[];shots=[];notes=set()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=executable_path,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            context=browser.new_context(viewport={'width':m.width_px,'height':m.height_px},device_scale_factor=1,
                java_script_enabled=False,service_workers='block',accept_downloads=False,reduced_motion='reduce' if m.kind=='reduced' else 'no-preference')
            context.route('**/*',lambda route:route.abort())
            page=context.new_page();page.set_default_timeout(10000)
            page.set_content(text,wait_until='load');page.evaluate('document.fonts.ready')
            for index in spec.frame_indices:
                time=frame_time_ms(index,m.fps)
                measured=page.evaluate(INSPECT,dict(time=float(time),expected=[o.object_id for o in policy.objects]))
                notes.update(measured['unsupported'])
                shot=save('frame-'+str(index)+'.png',page.screenshot(type='png',animations='allow',timeout=10000),capture_id+'-png-'+str(index))
                shots.append(shot)
                rows.append(dict(frame_index=index,time_numerator=time.numerator,time_denominator=time.denominator,screenshot_sha256=shot.sha256,objects=measured['objects']))
            renderer='Chromium '+browser.version
        finally:browser.close()
    payload=dict(schema_version='1.0.0',mode='paused-css-samples',plan_digest=request.plan_digest,policy_digest=policy.content_digest,
                 mode_id=mode_id,html_sha256=html_ref.sha256,renderer=renderer,viewport=[m.width_px,m.height_px],frames=rows,unsupported=sorted(notes))
    obs=save('observations.json',canonical_bytes(payload),capture_id+'-observations')
    return CaptureRef(capture_id,mode_id,html_ref,obs,tuple(shots))
