"""Five deterministic visual evaluators over bounded states and byte-linked text.

This evaluates declared screen geometry and optional static Chromium captures.
It does not infer arbitrary diagram meaning, certify every frame, or authorize release.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
import math,unicodedata
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from ..source_v2.io import SnapshotStore
from ..director_v2.metrics import merged_text
from .models import VisualRequest,VisualPolicy,Rect,TEXT_ROLES
from .geometry import contains,intersection,union_area,area_ppm,grid_peak,gap_squared,contrast_ratio
from .attestation import Review,ReviewVerifier,review_targets
from .adapters import to_native
from .capture_evidence import verify_capture

AREAS=('representation','layout','clutter','readability','alignment')
TASKS=dict(zip(AREAS,[f'BIE-QA-VIS-00{i}' for i in range(1,6)]))
LIMITATIONS=(
    'Geometry is axis-aligned milli-CSS-pixel bounding-box QA. It is not arbitrary pixel segmentation, 3D occlusion, exact glyph shape or continuous motion proof.',
    'Representation suitability, graphical meaning, source-to-visual mapping, glyph coverage and educational appropriateness require governed contextual review. Authentication proves identity, not assessor correctness.',
    'Clutter, type size and exposure limits are operator-controlled guardrails, not empirical cognitive-load or learner-comprehension measurements.',
    'Optional static HTML captures verify browser-observed rectangles/text and artifact bytes at listed viewports only. They are not native Remotion compilation, video playback, game execution or exhaustive runtime coverage.',
    'Uniform opaque sRGB background contrast is supported. Unknown backgrounds, transforms, filters, complex stacking and unsupported content require review rather than fabricated certainty.',
    'No full-media gate PASS, scientific learning efficacy, enterprise acceptance, current-HEAD migration or full-repository regression is implied.',
)


@dataclass(frozen=True,slots=True)
class VisualResult:
    source: EvaluationPair
    representation: Report
    layout: Report
    clutter: Report
    readability: Report
    alignment: Report
    native_layout_fingerprints: tuple[tuple[str,str],...]
    verified_capture_ids: tuple[str,...]
    @property
    def status(self):
        values=[self.source.grounding.status,self.source.provenance.status]+[getattr(self,k).status for k in AREAS]
        return 'BLOCKED' if 'BLOCKED' in values else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in values else 'CHECKS_PASSED')
    @property
    def product_accepted(self): return False
    def to_dict(self):
        d={k:getattr(self,k).to_dict() for k in ('source',)+AREAS}
        d.update(status=self.status,product_accepted=False,native_layout_fingerprints=self.native_layout_fingerprints,
                 verified_capture_ids=self.verified_capture_ids,continuous_media_verified=False)
        return d
    @property
    def content_digest(self): return digest(self.to_dict())


def evaluate(request,artifact_root,policy,*,as_of,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not VisualRequest or type(policy) is not VisualPolicy: raise ContractError('VIS_EVALUATION_INPUT_TYPE')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>8192 or any(type(r) is not Review for r in reviews): raise ContractError('VIS_REVIEW_COLLECTION')
    if len({r.review_id for r in reviews})!=len(reviews): raise ContractError('VIS_DUPLICATE_REVIEW_ID')
    if len({(r.purpose,r.subject_id,r.evaluator_id) for r in reviews})!=len(reviews): raise ContractError('VIS_DUPLICATE_REVIEW_VOTE')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier: raise ContractError('VIS_REVIEW_VERIFIER_TYPE')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={k:[] for k in ('common',)+AREAS}
    groups['common'].extend(source.grounding.findings+source.provenance.findings)
    def add(area,code,subject,detail,severity='BLOCKER'):
        groups[area].append(Finding(code,severity,subject,'VIS',detail))
    rd,pd=request.content_digest,policy.content_digest
    targets=review_targets(request,policy); valid=set(); tainted=set(); groups_approved={}
    for r in reviews:
        t=(r.purpose,r.subject_id)
        if t not in targets:
            add('common','VIS_UNKNOWN_REVIEW_TARGET',r.subject_id,'Unexpected assessment cannot expand the approved inventory.');continue
        if set(r.evidence_ids)!=set(targets[t]):
            add('common','VIS_REVIEW_EVIDENCE_MISMATCH',r.subject_id,'Assessment must bind the exact evidence identities.');tainted.add(t);continue
        auth=verifier.verify_bound(r,rd,pd,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:
            add('common','VIS_'+auth.code,r.subject_id,'Assessment authentication failed.');tainted.add(t)
        elif not auth.operational:
            add('common','VIS_TEST_ONLY_ASSESSMENT',r.subject_id,'Test-only authentication cannot authorize a production judgment.','REVIEW');tainted.add(t)
        elif r.verdict=='REJECTED':
            add('common','VIS_REVIEW_REJECTED',r.subject_id,'A reviewed rejection cannot be outvoted.');tainted.add(t)
        elif r.verdict!='VERIFIED' or r.confidence_ppm<policy.minimum_review_confidence_ppm:
            add('common','VIS_REVIEW_UNCERTAIN',r.subject_id,'Uncertain contextual support requires review.','REVIEW');tainted.add(t)
        else:
            groups_approved.setdefault(t,set()).add(auth.independence_group)
            if len(groups_approved[t])>=policy.minimum_independent_assessors: valid.add(t)
    approved=valid-tainted
    for t in sorted(set(targets)-approved):
        add('common','VIS_CONTEXT_REVIEW_MISSING',t[1],'Current authorized contextual assessment is required.','REVIEW')
    if (request.lesson_id,request.audience_id,request.language)!=(policy.lesson_id,policy.audience_id,policy.language):
        add('common','VIS_SCOPE_CONTEXT_MISMATCH','visual-scope','Lesson, audience and language are operator-controlled.')
    scenes={s.scene_id:s for s in request.scenes}; elements={e.object_id:e for e in request.elements}
    state_specs={s.state_id:s for s in policy.states};scene_specs={s.scene_id:s for s in policy.scenes}
    element_specs={e.object_id:e for e in policy.elements};views={v.view_id:v for v in policy.views}
    relations={r.relation_id:r for r in request.relations};states={s.state_id:s for s in request.states}
    claims={c.claim_id:c for c in request.source.claims};channels={o.output_id:o.channel for o in request.source.outputs}
    for actual,expected,label in [(set(scenes),set(scene_specs),'SCENE'),(set(elements),set(element_specs),'ELEMENT'),(set(states),set(state_specs),'STATE'),(set(relations),{r.relation_id for r in policy.relations},'RELATION')]:
        if actual!=expected: add('common','VIS_'+label+'_SCOPE_MISMATCH','visual-scope','Missing or added members cannot redefine the operator inventory.')
    for e in request.elements:
        if e!=element_specs.get(e.object_id): add('alignment','VIS_ELEMENT_SPEC_CHANGED',e.object_id,'Roles, source claims and semantics cannot be relabeled by the candidate.')
        if e.scene_id not in scenes or not set(e.claim_ids)<=set(claims): add('common','VIS_ELEMENT_REFERENCE',e.object_id,'Scene and claim references must resolve.')
        if e.claim_ids and set(e.encodings)=={'color'}:
            add('alignment','VIS_COLOR_ONLY_ENCODING',e.object_id,'Semantic distinction must not depend solely on color.')
    if set().union(*(set(e.claim_ids) for e in request.elements),*(set(r.claim_ids) for r in request.relations))!=set(claims):
        add('alignment','VIS_UNMAPPED_SOURCE_CLAIM','visual-scope','Every supplied visual-output claim must map to an approved element or relation.')
    for s in request.scenes:
        spec=scene_specs.get(s.scene_id)
        if spec and (s.representation not in spec.allowed_representations or set(s.objective_ids)!=set(spec.objective_ids) or not set(spec.required_features)<=set(s.features)):
            add('representation','VIS_REPRESENTATION_MISMATCH',s.scene_id,'Chosen representation lacks an approved purpose, type or essential feature.')
        if not any(e.scene_id==s.scene_id and e.role not in ('background','container') for e in request.elements):
            add('representation','VIS_EMPTY_EDUCATIONAL_SCENE',s.scene_id,'Decorative backgrounds are not explanatory content.')
    for r in request.relations:
        if r not in policy.relations or not {r.from_id,r.to_id}<=set(elements) or not set(r.claim_ids)<=set(claims):
            add('alignment','VIS_RELATION_CHANGED_OR_UNBOUND',r.relation_id,'Endpoints, direction and source identity must match the approved relation.')
    allowances={(a.state_id,tuple(sorted((a.first_id,a.second_id)))):a for a in policy.overlaps}
    fingerprints=[];captured=[];inspected=set(source.provenance.inspected_artifact_ids)|set(source.grounding.inspected_artifact_ids)
    stats=dict(states=0,pairs=0,collisions=0,max_items=0,max_semantics=0,max_area=0,max_cell=0,max_text=0,min_font=10**9,min_contrast=21000000,text_runs=0,native_collisions=0)
    captures={c.capture_id:c for c in request.captures}; used_captures=set()
    for s in sorted(request.states,key=lambda s:s.state_id):
        spec=state_specs.get(s.state_id);view=views.get(s.view_id)
        if spec is None or view is None or (s.scene_id,s.view_id,s.start_ms,s.end_ms)!=(spec.scene_id,spec.view_id,spec.start_ms,spec.end_ms):
            add('common','VIS_STATE_CONTEXT_MISMATCH',s.state_id,'The candidate cannot remove a responsive view or change its time window.');continue
        mm={m.object_id:m for m in s.measurements}
        if set(mm)!=set(spec.object_ids): add('common','VIS_STATE_INVENTORY_MISMATCH',s.state_id,'Hidden, missing and unexpected elements must remain observable.')
        if s.geometry_mode=='sampled': add('layout','VIS_CONTINUOUS_GEOMETRY_UNPROVEN',s.state_id,'A sample is not proof of every intermediate animation frame.','REVIEW')
        if s.capture_id!='none':
            cap=captures.get(s.capture_id);used_captures.add(s.capture_id)
            if cap is None or cap.state_id!=s.state_id:
                add('common','VIS_CAPTURE_REFERENCE',s.state_id,'Capture identity must resolve to this exact state.')
            else:
                try:
                    with SnapshotStore(artifact_root) as store:
                        unsupported=verify_capture(cap,s,view,store)
                    captured.append(cap.capture_id);inspected.update((cap.html.artifact_id,cap.measurements.artifact_id,cap.screenshot.artifact_id))
                    for code in unsupported:
                        add('common','VIS_CAPTURE_UNSUPPORTED',s.state_id,'Browser capture reports unsupported content: '+code,'REVIEW')
                except ContractError as exc: add('common',exc.code,s.state_id,'Capture bytes, binding or decoded image failed verification.')
        elif policy.require_captures:
            add('common','VIS_CAPTURE_REQUIRED',s.state_id,'Operator-required browser measurements are missing.','REVIEW')
        canvas=Rect(0,0,view.width_px*1000,view.height_px*1000);tol=policy.limits.geometry_tolerance_mpx
        valid_measurements=[]
        for m in s.measurements:
            e=elements.get(m.object_id)
            if not e or e.scene_id!=s.scene_id: add('common','VIS_MEASUREMENT_REFERENCE',m.object_id,'Measured object must belong to this scene.');continue
            if not m.displayed or m.opacity_ppm<policy.limits.min_opacity_ppm:
                add('layout','VIS_REQUIRED_ELEMENT_HIDDEN',m.object_id,'An expected teaching element is hidden or insufficiently opaque.')
            if not contains(canvas,m.box,tol) or not contains(m.clip,m.box,tol):
                add('layout','VIS_ELEMENT_CROPPED',m.object_id,'Element extent leaves its viewport or clipping rectangle.')
            if e.role not in ('background','container') and not contains(view.safe,m.box,tol):
                add('layout','VIS_SAFE_AREA_OVERFLOW',m.object_id,'Instructional content leaves the approved safe area.')
            if e.role not in ('caption','background','container') and any(intersection(m.box,r) for r in view.subtitle_regions):
                add('layout','VIS_SUBTITLE_ZONE_COLLISION',m.object_id,'Teaching content occupies a reserved caption region.')
            for flag in m.unsupported: add('common','VIS_UNSUPPORTED_GEOMETRY_OR_STYLE',m.object_id,'Unresolved rendered condition: '+flag,'REVIEW')
            if e.role in TEXT_ROLES or m.text:
                stats['text_runs']+=1;stats['min_font']=min(stats['min_font'],m.font_mpx)
                try: expected=merged_text(claims,e.claim_ids)
                except (ContractError,KeyError): expected=None
                if not m.text or expected!=m.text: add('alignment','VIS_DISPLAY_TEXT_MISMATCH',m.object_id,'Displayed text must match inspected output spans exactly.')
                if any(channels.get(claims[c].output_id) not in ('on_screen','caption','game_prompt','game_feedback','lesson') for c in e.claim_ids if c in claims):
                    add('alignment','VIS_TEXT_CHANNEL_MISMATCH',m.object_id,'Narration-only text is not evidence of screen presentation.')
                if e.role in ('background','container'): add('readability','VIS_TEXT_ROLE_BYPASS',m.object_id,'Text cannot avoid readability checks by a decorative role.')
                if m.font_mpx<policy.limits.min_font_mpx: add('readability','VIS_FONT_TOO_SMALL',m.object_id,'Measured text is below the configured size floor.')
                if not m.fonts_loaded: add('readability','VIS_FONTS_NOT_READY',m.object_id,'Measurements were taken before fonts were ready.','REVIEW')
                if not m.line_boxes: add('readability','VIS_TEXT_EXTENT_MISSING',m.object_id,'Text requires actual or declared line extents, not just a container.','REVIEW')
                if any(not contains(m.box,r,tol) or not contains(m.clip,r,tol) or not contains(canvas,r,tol) for r in m.line_boxes):
                    add('readability','VIS_TEXT_OVERFLOW',m.object_id,'Text line extent is clipped or outside its owner.')
                if any(unicodedata.category(c)=='Cc' and c not in '\n\t' or c=='\ufffd' for c in m.text):
                    add('readability','VIS_INVALID_TEXT_CHARACTERS',m.object_id,'Controls or replacement characters remain in displayed text.')
                duration=s.end_ms-s.start_ms
                if duration<policy.limits.min_text_exposure_ms or len(m.text)*60000>policy.limits.max_read_codepoints_per_minute*duration:
                    add('readability','VIS_TEXT_EXPOSURE_INSUFFICIENT',m.object_id,'Text exceeds the configured exposure or code-point-rate budget.')
                if not m.background_known or m.background.a!=255:
                    add('readability','VIS_CONTRAST_UNRESOLVED',m.object_id,'Unknown or nonuniform background cannot receive an average-color contrast pass.','REVIEW')
                else:
                    ratio=contrast_ratio(m.foreground,m.background,m.opacity_ppm)
                    stats['min_contrast']=min(stats['min_contrast'],math.floor(ratio*1000000))
                    if ratio<policy.limits.min_contrast_ppm/1000000:
                        add('readability','VIS_CONTRAST_TOO_LOW',m.object_id,'Unrounded sRGB contrast is below the configured threshold.')
            valid_measurements.append(m)
        for i,a in enumerate(valid_measurements):
            for b in valid_measurements[i+1:]:
                if not a.displayed or not b.displayed or a.opacity_ppm==0 or b.opacity_ppm==0: continue
                stats['pairs']+=1;inter=intersection(a.box,b.box)
                if inter is None: continue
                allow=allowances.get((s.state_id,tuple(sorted((a.object_id,b.object_id)))))
                okay=bool(allow and ('support',allow.allowance_id) in approved and inter.area*1000000<=allow.max_overlap_ppm*min(a.box.area,b.box.area))
                if not okay:
                    stats['collisions']+=1
                    add('layout','VIS_LAYOUT_COLLISION',s.state_id,'Unapproved overlap: '+a.object_id+' / '+b.object_id)
        foreground=[m for m in valid_measurements if m.displayed and m.opacity_ppm>0 and elements[m.object_id].role not in ('container','background')]
        boxlist=[m.box for m in foreground];items=len(foreground);semantic_count=len({elements[m.object_id].semantic_id for m in foreground})
        occupancy=area_ppm(boxlist,view.safe);peak=grid_peak(boxlist,view.safe,policy.limits.grid_rows,policy.limits.grid_columns)
        chars=sum(len(m.text) for m in foreground);stats['states']+=1
        for key,value in [('max_items',items),('max_semantics',semantic_count),('max_area',math.ceil(occupancy)),('max_cell',peak),('max_text',chars)]: stats[key]=max(stats[key],value)
        for code,bad,detail in [
            ('VIS_CLUTTER_ITEM_LIMIT',items>policy.limits.max_visible_items,'Too many simultaneous foreground elements.'),
            ('VIS_CLUTTER_SEMANTIC_LIMIT',semantic_count>policy.limits.max_semantic_items,'Too many simultaneous semantic items.'),
            ('VIS_CLUTTER_AREA_LIMIT',occupancy>policy.limits.max_area_ppm,'Foreground rectangle-union area exceeds the guardrail.'),
            ('VIS_CLUTTER_LOCAL_DENSITY',peak>policy.limits.max_cell_items,'One spatial cell exceeds the local-density guardrail.'),
            ('VIS_CLUTTER_TEXT_LIMIT',chars>policy.limits.max_text_codepoints,'Simultaneous text exceeds the configured guardrail.'),
            ('VIS_CONCURRENT_READING_RATE',chars*60000>policy.limits.max_read_codepoints_per_minute*(s.end_ms-s.start_ms),'Combined text streams exceed the reading budget.'),
        ]:
            if bad: add('clutter',code,s.state_id,detail)
        for rid in spec.relation_ids:
            rel=relations.get(rid)
            if not rel or rel.from_id not in mm or rel.to_id not in mm:
                add('alignment','VIS_RELATION_NOT_PRESENTED',rid,'Both approved relation endpoints must be present together.');continue
            a,b=mm[rel.from_id],mm[rel.to_id]
            if not a.displayed or not b.displayed: add('alignment','VIS_RELATION_ENDPOINT_HIDDEN',rid,'A hidden endpoint does not explain a relation.')
            wrong=(rel.kind=='left_of' and a.box.right>b.box.x+tol or rel.kind=='above' and a.box.bottom>b.box.y+tol or
                   rel.kind=='contains' and not contains(a.box,b.box,tol) or rel.kind=='label_for' and gap_squared(a.box,b.box)>policy.limits.label_distance_mpx**2)
            if wrong: add('alignment','VIS_SPATIAL_RELATION_VIOLATED',rid,'Measured geometry contradicts the approved spatial relation.')
        try:
            native,collisions=to_native(request,s,view);fingerprints.append((s.state_id,native.fingerprint));stats['native_collisions']+=len(collisions)
        except (ValueError,KeyError):
            add('layout','VIS_NATIVE_LAYOUT_REJECTED',s.state_id,'Pinned layout contract rejects the normalized projection; no native acceptance flag is used.')
    if set(captures)!=used_captures: add('common','VIS_UNUSED_CAPTURE','visual-scope','Unconsumed capture evidence cannot count toward coverage.')
    evidence=digest(dict(source=source.to_dict(),reviews=[asdict(r) for r in sorted(reviews,key=lambda x:x.review_id)],trust=verifier.configuration_digest,
                         verified_captures=sorted(captured),native_fingerprints=sorted(fingerprints)))
    stats['min_font']=0 if stats['min_font']==10**9 else stats['min_font']
    if not stats['text_runs']: stats['min_contrast']=0
    measurements={
        'representation':(('scenes_checked',len(scenes)),),
        'layout':(('states_checked',stats['states']),('pair_checks',stats['pairs']),('unapproved_collisions',stats['collisions']),('native_pair_collisions',stats['native_collisions']),('verified_static_captures',len(captured))),
        'clutter':tuple((k,stats[k]) for k in ('max_items','max_semantics','max_area','max_cell','max_text')),
        'readability':tuple((k,stats[k]) for k in ('text_runs','min_font','min_contrast')),
        'alignment':(('relations_checked',len(relations)),('elements_checked',len(elements))),
    }
    def report(k):
        fs=tuple(sorted(set(groups['common']+groups[k]),key=lambda f:(f.subject_id,f.code,f.severity,f.detail)))
        return Report(TASKS[k],request.content_digest,policy.content_digest,evidence,as_of,fs,measurements[k],tuple(sorted(inspected)),LIMITATIONS)
    return VisualResult(source,*(report(k) for k in AREAS),tuple(sorted(fingerprints)),tuple(sorted(captured)))


def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not VisualResult or actual!=expected: raise ContractError('VIS_STALE_OR_EDITED_REPORT')
    return actual


def evaluate_representation(*args,**kwargs): return evaluate(*args,**kwargs).representation

def evaluate_layout(*args,**kwargs): return evaluate(*args,**kwargs).layout

def evaluate_clutter(*args,**kwargs): return evaluate(*args,**kwargs).clutter

def evaluate_readability(*args,**kwargs): return evaluate(*args,**kwargs).readability

def evaluate_alignment(*args,**kwargs): return evaluate(*args,**kwargs).alignment
