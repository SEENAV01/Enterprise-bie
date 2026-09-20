"""H3-002: validate exhaustive source-bound *measured* layout observations.

The caller supplies evidence from a trusted runner. A hash binds bytes but is not
an attestation. Test-bridge or caller-supplied evidence cannot authorize rendering.
"""
from __future__ import annotations
from dataclasses import asdict
from .qa_common import QAFinding, ordered_findings, CompilerQAError, digest
from .frame_layout import finite, dimensions, layout_policy
from .artifact_hashing import require_sha256

BRIDGE_SCOPE = 'REAL_CHROMIUM_WHOLE_SCENE_WITH_EXPLICIT_REACT_REMOTION_TEST_DOUBLES'
DECLARED_SCOPE = 'DECLARED_EXTERNAL_MEASUREMENTS_NOT_ATTESTED'
EPS = .75  # CSS subpixel/DOM box tolerance only, not a legibility threshold.


def rect(v, name):
    if not isinstance(v,(list,tuple)) or len(v)!=4:
        raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: '+name+' needs x,y,width,height')
    values=[finite(x,name) for x in v]
    if values[2]<0 or values[3]<0:
        raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: negative extent')
    return values


def contains(a,b):
    return b[0]>=a[0]-EPS and b[1]>=a[1]-EPS and b[0]+b[2]<=a[0]+a[2]+EPS and b[1]+b[3]<=a[1]+a[3]+EPS


def inspect_content_fit(report, raw, target, manifest_sha256):
    require_sha256(manifest_sha256)
    policy=layout_policy(raw);count=dimensions(raw,target)
    ids={e['element_id'] for e in raw['elements']};findings=[]
    def error(code,message,path='$.measurements'):findings.append(QAFinding(code,'ERROR',message,path))
    if not isinstance(report,dict):raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: report object required')
    if report.get('scope') not in {BRIDGE_SCOPE,DECLARED_SCOPE}:
        error('LAYOUT_EVIDENCE_SCOPE_UNTRUSTED','Unknown evidence scope; an asserted real-Remotion flag is not an attestation.')
    expected={'scene_identity':digest(raw),'manifest_sha256':manifest_sha256,'width':target.width,'height':target.height,'fps':target.fps,'frame_count':count}
    for field,value in expected.items():
        if type(report.get(field)) is not type(value) or report.get(field)!=value:
            error('LAYOUT_EVIDENCE_IDENTITY_MISMATCH',field+' does not match the checked scene')
    if report.get('browser_errors') != []:error('LAYOUT_BROWSER_ERROR','Browser execution must report an empty error list')
    if report.get('fonts_ready') is not True:error('LAYOUT_FONTS_NOT_READY','Font readiness was not established')
    records=report.get('records')
    if not isinstance(records,list) or len(records)>count*len(ids):
        raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: bounded element-frame list required')
    observed=set();seen_codes={}
    def per_record(code,eid,frame,message):
        key=(code,eid)
        seen_codes.setdefault(key,{'first':frame,'count':0,'message':message})['count']+=1
    for i,row in enumerate(records):
        if not isinstance(row,dict):raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: invalid observation')
        eid,f=row.get('element_id'),row.get('frame')
        if not isinstance(eid,str) or eid not in ids or type(f) is not int or not 0<=f<count:
            error('LAYOUT_FRAME_UNKNOWN','Unknown element or frame in measurement');continue
        key=(eid,f)
        if key in observed:error('LAYOUT_FRAME_DUPLICATE',eid+' duplicates frame '+str(f));continue
        observed.add(key)
        if type(row.get('visible')) is not bool:raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: visibility must be explicit boolean')
        box=rect(row.get('layer_box'), 'layer_box')
        if row.get('scroll_overflow') not in (True,False) or type(row.get('scroll_overflow')) is not bool:
            raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: scroll overflow must be explicit boolean')
        text_boxes=row.get('text_boxes');ink=row.get('ink_boxes')
        if not isinstance(text_boxes,list) or not isinstance(ink,list) or len(text_boxes)+len(ink)>4096:
            raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: bounded text/ink lists required')
        checked_ink=[rect(v,'ink box') for v in ink]
        checked_text=[]
        for label in text_boxes:
            if not isinstance(label,dict):raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: text record required')
            b=rect(label.get('box'),'text box');size=finite(label.get('font_px'),'font_px')
            if size<0:raise CompilerQAError('LAYOUT_MEASUREMENT_INVALID: negative font size')
            checked_text.append((b,size))
        em=row.get('equation_em_px')
        if em is not None:em=finite(em,'equation_em_px')
        if not row['visible']:continue
        viewport=[0,0,target.width,target.height]
        if box[2]<=0 or box[3]<=0:per_record('LAYOUT_EMPTY_VISIBLE_LAYER',eid,f,'Visible layer has no measurable extent')
        if row['scroll_overflow']:per_record('LAYOUT_CONTENT_OVERFLOW',eid,f,'Content exceeds its layout box')
        for b in checked_ink:
            if not contains(viewport,b):per_record('LAYOUT_INK_OUTSIDE_VIEWPORT',eid,f,'Measured ink is outside viewport')
        for b,size in checked_text:
            if not contains(box,b):per_record('LAYOUT_TEXT_OUTSIDE_OWNER',eid,f,'Measured text or legend lies outside its owner')
            if not contains(viewport,b):per_record('LAYOUT_TEXT_OUTSIDE_VIEWPORT',eid,f,'Measured text leaves viewport')
            if size<policy['min_text_px']:per_record('LAYOUT_TEXT_BELOW_MINIMUM',eid,f,'Effective text size is below declared technical floor')
        if em is not None and em<policy['min_equation_px']:
            per_record('LAYOUT_EQUATION_BELOW_MINIMUM',eid,f,'Equation effective em is below declared technical floor')
    if len(observed)!=count*len(ids):error('LAYOUT_FRAME_COVERAGE_INCOMPLETE','Expected every element at every rendered frame; no sampled pass')
    for (code,eid),info in seen_codes.items():
        error(code,info['message']+'; element='+eid+', first_frame='+str(info['first'])+', occurrences='+str(info['count']))
    fs=ordered_findings(findings)
    return {'schema_version':'bie.content-fit.v1','scope':report.get('scope'),'findings':[asdict(f) for f in fs],
            'passed':not fs,'records_expected':count*len(ids),'records_checked':len(observed),
            'evidence_sha256':digest(report),'manifest_sha256':manifest_sha256,
            'real_remotion_verified':False,'release_authorized':False,'accepted':False,
            'limits':'Measured DOM/geometry checks; no automatic text rewriting, universal contrast, pedagogy or ink segmentation claim.'}


def require_real_layout_authorization(receipt):
    """No currently implemented browser bridge is a production renderer witness."""
    raise CompilerQAError('REAL_LAYOUT_EVIDENCE_REQUIRED: test-bridge/caller measurements are not real Remotion frame acceptance')
