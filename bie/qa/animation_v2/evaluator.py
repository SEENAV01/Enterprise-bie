"""Animation temporal, excessive-motion and semantic consistency evaluators."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from math import ceil,isqrt
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from ..source_v2.io import SnapshotStore
from .models import AnimationRequest,AnimationPolicy
from .metrics import SUPPORTED,violates_timing,invariant_counterexample,trajectory_motion
from .attestation import Review,ReviewVerifier,review_targets
from .capture_evidence import verify_capture
from .adapters import native_diagnostics

AREAS=('temporal','motion','alignment')
TASKS=dict(zip(AREAS,('BIE-QA-ANI-001','BIE-QA-ANI-002','BIE-QA-ANI-003')))
LIMITATIONS=(
    'Exact declared scalar 2-D linear/step trajectories and rational frame clocks, not general CSS, springs, 3-D occlusion, physical simulation, or measured audiovisual synchronization.',
    'Motion thresholds are operator guardrails, not clinical safety certification, a photosensitive-flash test, or empirically calibrated learning/comfort measurements.',
    'Contextual interpretation and scientific animation meaning require calibrated authorized assessments. Authentication is identity, not correctness.',
    'Paused CSS browser samples bind inspected HTML/observation/PNG bytes at prescribed frames; they cannot prove unsampled behavior, real-time playback, audio, native Remotion or game execution.',
    'No complete-media gate PASS, production capture attestation, full canonical regression, GitHub integration, real-book E2E or enterprise acceptance is implied.')

@dataclass(frozen=True,slots=True)
class AnimationResult:
    source: EvaluationPair
    temporal: Report
    motion: Report
    alignment: Report
    native_diagnostics: tuple[tuple[str,str,str],...]
    verified_capture_ids: tuple[str,...]
    @property
    def status(self):
        states=[self.source.grounding.status,self.source.provenance.status]+[getattr(self,k).status for k in AREAS]
        return 'BLOCKED' if 'BLOCKED' in states else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in states else 'CHECKS_PASSED'
    @property
    def product_accepted(self):return False
    def to_dict(self):
        return dict(source=self.source.to_dict(),**{k:getattr(self,k).to_dict() for k in AREAS},status=self.status,product_accepted=False,
                    native_diagnostics=self.native_diagnostics,verified_capture_ids=self.verified_capture_ids,complete_media_verified=False)
    @property
    def content_digest(self):return digest(self.to_dict())

def evaluate(request,artifact_root,policy,*,as_of,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not AnimationRequest or type(policy) is not AnimationPolicy:raise ContractError('ANI_EVALUATION_INPUT_TYPE')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>8192 or any(type(r) is not Review for r in reviews):raise ContractError('ANI_REVIEW_COLLECTION')
    if len({r.review_id for r in reviews})!=len(reviews):raise ContractError('ANI_DUPLICATE_REVIEW_ID')
    if len({(r.purpose,r.subject_id,r.evaluator_id) for r in reviews})!=len(reviews):raise ContractError('ANI_DUPLICATE_REVIEW_VOTE')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('ANI_VERIFIER_TYPE')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={k:[] for k in ('common',)+AREAS};groups['common'].extend(source.grounding.findings+source.provenance.findings)
    def add(area,code,subject,detail,severity='BLOCKER'):groups[area].append(Finding(code,severity,subject,'ANI',detail))
    targets=review_targets(request,policy);tainted=set();votes={}
    for r in reviews:
        t=(r.purpose,r.subject_id)
        if t not in targets:add('common','ANI_UNKNOWN_REVIEW_TARGET',r.subject_id,'Review does not match an approved purpose/subject.');continue
        if set(r.evidence_ids)!=set(targets[t]):
            add('common','ANI_REVIEW_EVIDENCE_MISMATCH',r.subject_id,'Exact evidence identities required.');tainted.add(t);continue
        auth=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:add('common','ANI_'+auth.code,r.subject_id,'Review authentication failed.');tainted.add(t)
        elif not auth.operational:add('common','ANI_TEST_ONLY_REVIEW',r.subject_id,'Test-only trust cannot authorize a contextual assessment.','REVIEW');tainted.add(t)
        elif r.verdict=='REJECTED':add('common','ANI_REVIEW_REJECTED',r.subject_id,'A rejection cannot be outvoted.');tainted.add(t)
        elif r.verdict!='VERIFIED' or r.confidence_ppm<policy.minimum_review_confidence_ppm:
            add('common','ANI_REVIEW_UNCERTAIN',r.subject_id,'Context needs review.','REVIEW');tainted.add(t)
        else:votes.setdefault(t,set()).add(auth.independence_group)
    for t in sorted(targets):
        if t in tainted or len(votes.get(t,()))<policy.minimum_independent_assessors:
            add('common','ANI_CONTEXT_REVIEW_MISSING',t[1],'Current, scoped, authorized contextual assessment is required.','REVIEW')
    if request.lesson_id!=policy.lesson_id:add('common','ANI_LESSON_CONTEXT','animation-scope','Lesson is operator-controlled.')
    if request.modes!=policy.modes:add('common','ANI_MODE_SCOPE','animation-scope','Frame rate, viewport, duration and reduced-mode inventory are operator-controlled.')
    if request.objects!=policy.objects:add('alignment','ANI_OBJECT_SCOPE','animation-scope','Object identity, lifetime and meaning cannot be silently replaced.')
    if request.cues!=policy.cues:add('temporal','ANI_CUE_SCOPE','animation-scope','Cue windows and source claims are operator-controlled, not candidate-adjustable.')
    tracks={t.track_id:t for t in request.tracks};specs={t.track_id:t for t in policy.tracks};modes={m.mode_id:m for m in policy.modes}
    objs={o.object_id:o for o in policy.objects};cues={c.cue_id:c for c in request.cues};claims={c.claim_id for c in request.source.claims}
    if set(tracks)!=set(specs):add('common','ANI_TRACK_INVENTORY','animation-scope','Missing or added tracks cannot redefine required educational coverage.')
    claimmap=set().union(*(set(s.claim_ids) for s in policy.tracks),*(set(o.claim_ids) for o in policy.objects),*(set(c.claim_ids) for c in policy.cues))
    if claimmap!=claims:add('alignment','ANI_SOURCE_CLAIM_COVERAGE','animation-scope','Every declared source/output claim and mapping must resolve without silent omission.')
    unsupported=0
    for t in sorted(request.tracks,key=lambda t:t.track_id):
        s=specs.get(t.track_id);m=modes.get(t.mode_id);o=objs.get(t.object_id)
        if s is None or m is None or o is None:add('common','ANI_TRACK_REFERENCE',t.track_id,'Unknown mode/object/requirement.');continue
        if any(getattr(s,n)!=getattr(t,n) for n in ('mode_id','object_id','property','semantic_id','purpose')):
            add('alignment','ANI_TRACK_MEANING_CHANGED',t.track_id,'The candidate cannot relabel movement, purpose or semantic identity.')
        if t.start_ms<o.start_ms or t.end_ms>o.end_ms or t.end_ms>m.duration_ms:
            add('temporal','ANI_TRACK_OUTSIDE_LIFETIME',t.track_id,'Animation must fit approved object and mode lifetimes.')
        if any(not s.minimum_value<=k.value<=s.maximum_value for k in t.keyframes):add('alignment','ANI_VALUE_RANGE',t.track_id,'Keyframe violates approved domain/bounds.')
        if t.property in ('opacity_ppm','progress_ppm') and any(not 0<=k.value<=1000000 for k in t.keyframes):add('alignment','ANI_PROPERTY_DOMAIN',t.track_id,'Opacity/progress must remain in [0,1].')
        if t.property=='scale_ppm' and any(k.value<=0 for k in t.keyframes):add('alignment','ANI_SCALE_DOMAIN',t.track_id,'Nonpositive scale is unsupported.')
        diffs=[b.value-a.value for a,b in zip(t.keyframes,t.keyframes[1:])]
        if s.trend=='increasing' and any(d<0 for d in diffs) or s.trend=='decreasing' and any(d>0 for d in diffs) or s.trend=='constant' and any(d!=0 for d in diffs):
            add('alignment','ANI_TREND_CONTRADICTION',t.track_id,'Intermediate keyframes contradict the required direction, not only the endpoints.')
        if s.endpoints_required and (abs(t.keyframes[0].value-s.start_value)>s.tolerance or abs(t.keyframes[-1].value-s.end_value)>s.tolerance):
            add('alignment','ANI_ENDPOINT_MEANING',t.track_id,'Start/end state does not preserve the approved educational result.')
        for cid in s.disclosure_cue_ids:
            c=cues.get(cid)
            if c is None or c.start_ms>t.start_ms or c.end_ms<t.end_ms:add('alignment','ANI_DISCLOSURE_TIMING',t.track_id,'Condition/not-to-scale disclosure must accompany the entire transformation.')
        if t.interpolation not in SUPPORTED:
            unsupported+=1;add('common','ANI_UNSUPPORTED_INTERPOLATION',t.track_id,'Endpoints do not certify the interior of an unimplemented interpolation.','REVIEW')
        if o.role=='camera':add('motion','ANI_CAMERA_COMPOSITION_UNPROVEN',t.track_id,'Screen-wide camera/object composition requires rendered observation.','REVIEW')
    ts=sorted(request.tracks,key=lambda t:t.track_id)
    for i,a in enumerate(ts):
        for b in ts[i+1:]:
            if (a.mode_id,a.object_id,a.property)==(b.mode_id,b.object_id,b.property) and max(a.start_ms,b.start_ms)<min(a.end_ms,b.end_ms):
                add('temporal','ANI_CONFLICTING_PROPERTY_WRITERS',a.track_id+':'+b.track_id,'Overlapping writers to one property are not silently composited.')
    for rule in policy.timing_rules:
        left=tracks.get(rule.left_track_id);right=(tracks if rule.right_kind=='track' else cues).get(rule.right_id)
        if left is None or right is None:add('temporal','ANI_TIMING_REFERENCE',rule.rule_id,'Timing obligation is missing its target.')
        elif left.mode_id!=right.mode_id or violates_timing(rule,left,right):add('temporal','ANI_TEMPORAL_MISALIGNMENT',rule.rule_id,'Approved relation/tolerance is violated.')
    violations,stats=trajectory_motion(request,policy)
    for code,subject,time in violations:add('motion',code,subject,'Measured declared-trajectory violation at '+str(time)+' ms.')
    invariants=0
    for rule in policy.invariants:
        if not set(rule.track_ids)<=set(tracks):add('alignment','ANI_INVARIANT_MISSING_TRACK',rule.invariant_id,'Invariant cannot omit a required member.');continue
        try:counter=invariant_counterexample(rule,tracks)
        except ContractError as exc:
            add('alignment',exc.code,rule.invariant_id,'Invariant coverage/interpolation cannot be certified.','REVIEW' if exc.code=='ANI_UNSUPPORTED_INTERPOLATION' else 'BLOCKER');continue
        invariants+=1
        if counter:add('alignment','ANI_SEMANTIC_INVARIANT',rule.invariant_id,'Counterexample '+str(counter))
    inspected=set(source.provenance.inspected_artifact_ids)|set(source.grounding.inspected_artifact_ids);caps=[];sample_count=0
    for capture in request.captures:
        try:
            with SnapshotStore(artifact_root) as store:errors,notes,count=verify_capture(capture,request,policy,store)
            inspected.update(a.artifact_id for a in (capture.html,capture.observations)+capture.screenshots)
            caps.append(capture.capture_id);sample_count+=count
            for code,subject,frame in errors:add('common',code,subject,'Browser observation differs at prescribed frame '+str(frame)+'.')
            for note in notes:add('common','ANI_CAPTURE_UNSUPPORTED',capture.capture_id,note,'REVIEW')
            add('common','ANI_SAMPLED_MEDIA_ONLY',capture.capture_id,'Paused samples do not certify continuous playback or production capture authenticity.','REVIEW')
        except ContractError as exc:add('common',exc.code,capture.capture_id,'Capture evidence failed byte/context/clock verification.')
    captured_modes={c.mode_id for c in request.captures if c.capture_id in caps}
    for spec in policy.captures:
        if spec.required and spec.mode_id not in captured_modes:add('common','ANI_CAPTURE_MISSING',spec.mode_id,'Required browser observations have not been verified.','REVIEW')
    diagnostics=native_diagnostics(request,policy)
    evidence=digest(dict(source=source.to_dict(),reviews=[asdict(r) for r in sorted(reviews,key=lambda r:r.review_id)],trust=verifier.configuration_digest,
                         native=diagnostics,captures=sorted(caps)))
    measurements={'temporal':(('tracks_checked',len(ts)),('timing_rules_checked',len(policy.timing_rules)),('verified_sample_frames',sample_count)),
                  'motion':(('peak_moving_objects',stats['peak_objects']),('peak_sum_normalized_rate_ppm_ceiling',ceil(stats['peak_sum_rate_ppm'])),('max_reversals',stats['max_reversals'])),
                  'alignment':(('invariants_checked',invariants),('unsupported_tracks',unsupported))}
    def report(k):
        fs=tuple(sorted(set(groups['common']+groups[k]),key=lambda f:(f.subject_id,f.code,f.severity,f.detail)))
        return Report(TASKS[k],request.content_digest,policy.content_digest,evidence,as_of,fs,measurements[k],tuple(sorted(inspected)),LIMITATIONS)
    return AnimationResult(source,*(report(k) for k in AREAS),diagnostics,tuple(sorted(caps)))

def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not AnimationResult or actual!=expected:raise ContractError('ANI_STALE_OR_EDITED_REPORT')
    return actual

def evaluate_temporal(*args,**kwargs):return evaluate(*args,**kwargs).temporal

def evaluate_motion(*args,**kwargs):return evaluate(*args,**kwargs).motion

def evaluate_alignment(*args,**kwargs):return evaluate(*args,**kwargs).alignment
