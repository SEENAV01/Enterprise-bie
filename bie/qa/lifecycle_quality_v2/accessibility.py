"""HARD024 output-accessibility evidence census and bounded observed checks.

This is not a WCAG conformance/clinical flash certificate. Actual native output,
caption meaning, screen-reader and physical-device evidence remain independent.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib
from .common import *
AXES=('keyboard','focus','color','captions','reduced_motion','flash')

@dataclass(frozen=True)
class AccessibilityPolicy:
    controls:tuple[str,...]
    viewports:tuple[str,...]
    required_meanings:tuple[str,...]
    caption_ids:tuple[str,...]
    axes:tuple[str,...]=AXES
    min_contrast:str='9/2'
    max_caption_rate:str='20'
    max_age_seconds:int=3600
    def __post_init__(self):
        for k in ('controls','viewports','required_meanings','caption_ids','axes'):ids(getattr(self,k),k,minimum=0 if k=='caption_ids' else 1)
        require(set(self.axes)<=set(AXES),'H6_ACCESS_AXIS')
        require(q(self.min_contrast)>=1 and q(self.max_caption_rate)>0,'H6_ACCESS_LIMIT')
        integer(self.max_age_seconds,'age',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))


def evaluate_accessibility(root,measurement,binding,policy,*,now):
    bind(binding,policy);integer(now,'now')
    doc=load(root,measurement)
    fields(doc,('schema_version','binding','created_at','execution_id','mode','artifacts','views'),'H6_ACCESS_FIELDS')
    require(doc['schema_version']=='bie.qa.output-accessibility/1','H6_ACCESS_SCHEMA');binding_matches(doc['binding'],binding)
    integer(doc['created_at'],'capture time');token(doc['execution_id'],'execution')
    require(doc['mode'] in ('NATIVE_OUTPUT','TRUSTED_STATIC_DIAGNOSTIC','SYNTHETIC_OBSERVATION'),'H6_ACCESS_MODE')
    findings=[];inspected=[measurement]
    if not 0<=now-doc['created_at']<=policy.max_age_seconds:blocker(findings,'ACCESS_CAPTURE_EXPIRED_OR_FUTURE')
    refs=tuple(ArtifactRef(**r) for r in items(doc['artifacts'],'capture artifacts',1,512))
    require(len({r.artifact_id for r in refs})==len(refs) and len({r.path for r in refs})==len(refs),'H6_ACCESS_ARTIFACT_ALIAS')
    for r in refs:read(root,r);inspected.append(r)
    views=unique(items(doc['views'],'views',1,64),'viewport_id','H6_ACCESS_VIEW_DUPLICATE')
    if set(views)!=set(policy.viewports):blocker(findings,'ACCESS_VIEWPORT_CENSUS')
    observed=0
    for vid,v in views.items():
        fields(v,('viewport_id','measured_axes','controls','meanings','captions','motion','flash'),'H6_ACCESS_VIEW_FIELDS')
        ids(v['measured_axes'],'measured_axes',minimum=0);require(set(v['measured_axes'])<=set(AXES),'H6_ACCESS_UNKNOWN_AXIS')
        missing=set(policy.axes)-set(v['measured_axes'])
        for a in sorted(missing):findings.append(Finding('ACCESS_AXIS_NOT_MEASURED',vid+':'+a))
        controls=unique(items(v['controls'],'controls',0,512),'control_id','H6_CONTROL_DUPLICATE')
        if set(controls)!=set(policy.controls):blocker(findings,'ACCESS_CONTROL_CENSUS',vid)
        for cid,c in controls.items():
            fields(c,('control_id','name','keyboard_reached','focus_indicator','visible','contrast'),'H6_ACCESS_CONTROL_FIELDS')
            for k in ('keyboard_reached','focus_indicator','visible'):require(type(c[k]) in (bool,type(None)),'H6_ACCESS_OBSERVATION_TYPE')
            if type(c['name']) is not str or not c['name'].strip():blocker(findings,'ACCESS_UNNAMED_CONTROL',cid)
            if c['visible'] is False:blocker(findings,'ACCESS_CONTROL_HIDDEN',cid)
            for axis,field,code in [('keyboard','keyboard_reached','ACCESS_KEYBOARD_UNREACHABLE'),('focus','focus_indicator','ACCESS_FOCUS_MISSING')]:
                if axis in policy.axes:
                    if c[field] is False:blocker(findings,code,cid)
                    elif c[field] is None:findings.append(Finding('ACCESS_MEASUREMENT_UNKNOWN',cid+':'+axis))
            if c['contrast'] is not None:
                if q(c['contrast'])<q(policy.min_contrast):blocker(findings,'ACCESS_CONTROL_CONTRAST',cid)
            else:findings.append(Finding('ACCESS_CONTRAST_UNKNOWN',cid))
            observed+=1
        meanings=unique(items(v['meanings'],'meanings',0,512),'meaning_id','H6_MEANING_DUPLICATE')
        if set(meanings)!=set(policy.required_meanings):blocker(findings,'ACCESS_MEANING_CENSUS',vid)
        for mid,m in meanings.items():
            fields(m,('meaning_id','non_color_label'),'H6_MEANING_FIELDS')
            if type(m['non_color_label']) is not str or not m['non_color_label'].strip():blocker(findings,'ACCESS_COLOR_ONLY_MEANING',mid)
        captions=unique(items(v['captions'],'captions',0,4096),'caption_id','H6_CAPTION_DUPLICATE')
        if set(captions)!=set(policy.caption_ids):blocker(findings,'ACCESS_CAPTION_CENSUS',vid)
        for cid,c in captions.items():
            fields(c,('caption_id','text','visible','start_ms','end_ms','contrast'),'H6_CAPTION_FIELDS')
            require(type(c['visible']) is bool,'H6_CAPTION_VISIBILITY_TYPE');text(c['text'],'caption')
            integer(c['start_ms'],'start');integer(c['end_ms'],'end',c['start_ms']+1)
            if not c['visible']:blocker(findings,'ACCESS_CAPTION_HIDDEN',cid)
            if q(len(c['text'])*1000)>q(policy.max_caption_rate)*(c['end_ms']-c['start_ms']):blocker(findings,'ACCESS_CAPTION_TOO_FAST',cid)
            if c['contrast'] is None:findings.append(Finding('ACCESS_CAPTION_CONTRAST_UNKNOWN',cid))
            elif q(c['contrast'])<q(policy.min_contrast):blocker(findings,'ACCESS_CAPTION_CONTRAST',cid)
        m=v['motion'];fields(m,('observed','mode','meaning_ids'),'H6_MOTION_FIELDS');require(type(m['observed']) is bool,'H6_MOTION_OBSERVATION')
        ids(m['meaning_ids'],'motion meanings',minimum=0)
        require(m['mode'] in ('standard','reduced','unknown'),'H6_MOTION_MODE')
        if m['observed'] and m['mode']=='reduced' and not set(policy.required_meanings)<=set(m['meaning_ids']):blocker(findings,'ACCESS_REDUCED_MEANING_LOSS',vid)
        if 'reduced_motion' in policy.axes and (not m['observed'] or m['mode']!='reduced'):findings.append(Finding('ACCESS_REDUCED_OUTPUT_NOT_OBSERVED',vid))
        f=v['flash'];fields(f,('full_output_observed','screening','frame_count'),'H6_FLASH_FIELDS')
        require(type(f['full_output_observed']) is bool and f['screening'] in ('CLEAR','FAIL','UNKNOWN'),'H6_FLASH_TYPE');integer(f['frame_count'],'frame count')
        if f['screening']=='FAIL':blocker(findings,'ACCESS_FLASH_SCREENING_FAILED',vid)
        if 'flash' in policy.axes and (not f['full_output_observed'] or f['screening']=='UNKNOWN' or f['frame_count']==0):findings.append(Finding('ACCESS_FLASH_COVERAGE_UNVERIFIED',vid))
    if doc['mode']!='NATIVE_OUTPUT':findings.append(Finding('ACCESS_NATIVE_OUTPUT_NOT_VERIFIED','capture'))
    return result('BIE-QA-HARD-024',binding,findings,dict(controls_checked=observed,capture_mode=doc['mode'],
       axes_requested=policy.axes,conformance_certified=False,empirical_accessibility_verified=False),inspected)


def collect_static_keyboard(html_bytes,output,binding,policy,*,browser,now):
    """Actual keyboard traversal of trusted static diagnostic HTML only.

    No native-origin fallback. External requests and authored scripts are disabled.
    Outline visibility is a CSS heuristic; actual contrast/paint remains unmeasured.
    """
    from playwright.sync_api import sync_playwright
    from ..media_runtime_v2.common import Tool
    bind(binding,policy);require(type(browser) is Tool,'H6_BROWSER_PIN');exe=browser.verify()
    require(policy.viewports==('desktop',),'H6_STATIC_VIEWPORT_PROFILE_UNSUPPORTED')
    require(type(html_bytes) is bytes and len(html_bytes)<=1024*1024,'H6_HTML_LIMIT')
    require(b'<script' not in html_bytes.lower(),'H6_STATIC_SCRIPT_REJECTED')
    out=Path(output);require(not out.exists(),'H6_CAPTURE_OUTPUT_EXISTS');out.mkdir(parents=True)
    p=out/'page.html';p.write_bytes(html_bytes);refs=[ArtifactRef('page-html','page.html',hashlib.sha256(html_bytes).hexdigest(),len(html_bytes),'support')]
    views=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox'])
        try:
            for vid in policy.viewports:
                ctx=b.new_context(java_script_enabled=False,viewport={'width':800,'height':600})
                ctx.route('**/*',lambda route:route.abort());page=ctx.new_page();page.set_content(html_bytes.decode('utf-8'))
                unfocused={}
                for cid in policy.controls:
                    loc=page.locator('[id="'+cid+'"]')
                    if loc.count()==1 and loc.is_visible():unfocused[cid]=loc.screenshot()
                observed={}
                for _ in range(len(policy.controls)*3+3):
                    page.keyboard.press('Tab')
                    c=page.evaluate('''() => {const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return {control_id:e.id,name:e.getAttribute('aria-label')||e.innerText||'',keyboard_reached:true,focus_indicator:s.outlineStyle!='none'&&parseFloat(s.outlineWidth)>0,visible:r.width>0&&r.height>0&&s.visibility!='hidden'&&s.display!='none'&&parseFloat(s.opacity)>0,contrast:null}}''')
                    if c['control_id'] in policy.controls:
                        if c['focus_indicator'] is False and c['control_id'] in unfocused:
                            from PIL import Image,ImageChops
                            from io import BytesIO
                            loc=page.locator('[id="'+c['control_id']+'"]')
                            a=Image.open(BytesIO(unfocused[c['control_id']])).convert('RGB');z=Image.open(BytesIO(loc.screenshot())).convert('RGB')
                            # An alternative paint change needs review; no false no-focus claim.
                            if a.size!=z.size or ImageChops.difference(a,z).getbbox() is not None:c['focus_indicator']=None
                        observed[c['control_id']]=c
                for cid in policy.controls:
                    if cid not in observed:
                        loc=page.locator('[id="'+cid+'"]');name=loc.inner_text() if loc.count()==1 else ''
                        observed[cid]=dict(control_id=cid,name=name,keyboard_reached=False,focus_indicator=None,visible=loc.is_visible() if loc.count()==1 else False,contrast=None)
                png=page.screenshot(full_page=True);name=vid+'.png';(out/name).write_bytes(png)
                refs.append(ArtifactRef('capture-'+vid,name,hashlib.sha256(png).hexdigest(),len(png),'support'))
                views.append(dict(viewport_id=vid,measured_axes=['keyboard','focus'],controls=list(observed.values()),
                   meanings=[dict(meaning_id=k,non_color_label=page.locator('[data-meaning-id="'+k+'"]').inner_text() if page.locator('[data-meaning-id="'+k+'"]').count()==1 else '') for k in policy.required_meanings],captions=[],
                   motion=dict(observed=False,mode='unknown',meaning_ids=[]),flash=dict(full_output_observed=False,screening='UNKNOWN',frame_count=0)))
                ctx.close()
        finally:b.close()
    # Literal labels are observed; semantic adequacy still requires independent review.
    doc=dict(schema_version='bie.qa.output-accessibility/1',binding=asdict(binding),created_at=now,
        execution_id='static-keyboard-'+hashlib.sha256(html_bytes).hexdigest()[:16],mode='TRUSTED_STATIC_DIAGNOSTIC',artifacts=[asdict(r) for r in refs],views=views)
    raw=canonical_bytes(doc);(out/'observation.json').write_bytes(raw)
    return ArtifactRef('access-observation','observation.json',hashlib.sha256(raw).hexdigest(),len(raw),'support')
