"""Complete scene views and transport evidence for bounded annotation execution."""
from dataclasses import asdict,dataclass,replace
from .director_artifacts import canonical,fingerprint,parse_json
from .director_model import DirectingAttempt,request_material,ResourceLimit
from .narration_annotations import AnnotationPolicy,annotation_payload
from .annotation_review import AnnotationReviewPolicy
from .context_windows import make_window,window_view,ordered_decisions
from .grounded_directing import model_context
from .qa_contract import snapshot_script


@dataclass(frozen=True)
class WindowedAnnotationPolicy(AnnotationPolicy):
    window_version:str='bie-dir-scene-annotations/1.0.0'
    maximum_windows:int=128
    def validate(self):
        super().validate()
        if self.window_version!='bie-dir-scene-annotations/1.0.0':raise ValueError('unknown annotation window policy')
        if type(self.maximum_windows) is not int or self.maximum_windows<1:raise ValueError('positive annotation window budget required')


@dataclass(frozen=True)
class WindowedAnnotationReviewPolicy(AnnotationReviewPolicy):
    window_version:str='bie-dir-scoped-annotation-review/1.0.0'
    maximum_windows:int=256
    def validate(self):
        super().validate()
        if self.window_version!='bie-dir-scoped-annotation-review/1.0.0':raise ValueError('unknown review window policy')
        if type(self.maximum_windows) is not int or self.maximum_windows<1:raise ValueError('positive review window budget required')


@dataclass(frozen=True)
class AnnotationBaseView:
    plan:object
    narrated_scenes:tuple
    execution:object
    generated_assessment_bindings:tuple


def scene_view(inputs,base,scene_ids):
    """Keep exact full utterances/offsets; this view is never published as a base."""
    wanted=set(scene_ids);actual=tuple(s.scene_id for s in base.plan.scenes if s.scene_id in wanted)
    if len(wanted)!=len(scene_ids) or actual!=tuple(scene_ids) or not actual:raise ValueError('ordered actual scene scope required')
    scenes=tuple(s for s in base.plan.scenes if s.scene_id in wanted)
    dids={d for s in scenes for d in s.pedagogy_decision_ids}
    window=make_window(inputs,tuple(d for d in ordered_decisions(inputs) if d in dids),1)
    view=window_view(inputs,window)
    snapshot=base.execution.snapshot;segments=tuple(s for s in snapshot.script.segments if s.scene_id in wanted)
    uids={s.segment_id for s in segments}
    part=snapshot_script(replace(snapshot.script,segments=segments),tuple(d for d in snapshot.drafts if d.segment_id in uids),
        tuple(u for u in snapshot.segment_order if u in uids),snapshot.language)
    # A scoped ScriptPlan has its own fingerprint. Text, IDs, ordering and
    # offsets remain exact; final annotations are rebound to the full snapshot.
    assert tuple(replace(u,script_fingerprint=snapshot.script.fingerprint()) for u in part.utterances)==tuple(u for u in snapshot.utterances if u.utterance_id in uids)
    plan=replace(base.plan,input_fingerprint=view.fingerprint(),scenes=tuple(replace(s,parent_scene_ids=tuple(p for p in s.parent_scene_ids if p in wanted)) for s in scenes))
    architecture=replace(base.execution.architecture,
        scenes=tuple(replace(s,parent_scene_ids=tuple(p for p in s.parent_scene_ids if p in wanted)) for s in base.execution.architecture.scenes if s.scene_id in wanted))
    part_base=AnnotationBaseView(plan,tuple(n for n in base.narrated_scenes if n.scene_id in wanted),
        replace(base.execution,snapshot=part,architecture=architecture),
        tuple(b for b in base.generated_assessment_bindings if b[1] in uids and b[2] in uids))
    return view,part_base


def scene_payload(inputs,base,scene_ids,policy):
    view,part=scene_view(inputs,base,scene_ids)
    payload=annotation_payload(view,part,policy)
    payload['global_input_fingerprint']=inputs.fingerprint()
    payload['global_snapshot_fingerprint']=base.execution.snapshot.fingerprint()
    payload['global_plan_fingerprint']=base.plan.fingerprint()
    payload['original_utterance_fingerprints']={u.utterance_id:u.fingerprint() for u in base.execution.snapshot.utterances if u.scene_id in scene_ids}
    payload['scene_scope']=list(scene_ids)
    payload['scope_fingerprint']=fingerprint(payload)
    return payload,view,part


def discourse_payload(inputs,base,policy):
    """All actual speech; exact supplied concept context, not page-truth review."""
    payload=annotation_payload(inputs,base,policy)
    full=payload['inputs']
    keep=('input_fingerprint','lesson_id','title','language','objectives','pedagogy','teaching_bindings','teaching_context','review_reasons')
    payload['inputs']={k:full[k] for k in keep if k in full}
    payload['scope']='COMPLETE_SPOKEN_LESSON_DISCOURSE; FULL_SOURCE_FACTS_REVIEWED_IN_SCENE_REQUESTS'
    payload['source_catalog_fingerprint']=inputs.catalog.fingerprint()
    payload['source_pages_in_this_request']=False
    return payload


@dataclass(frozen=True)
class ScopedAnnotationCall:
    scope_id:str
    scene_ids:tuple[str,...]
    request_payload_fingerprint:str
    response_json:str|None
    attempts:tuple[DirectingAttempt,...]
    failure:str|None=None


def verify_call(call,identity,policy,phase,subject,payload,schema,prompt,*,allow_failure=False):
    if (call.scope_id,call.request_payload_fingerprint)!=(subject,fingerprint(payload)):
        raise ValueError('scope does not bind actual source/narration/request context')
    last=None;success=False
    allowed={'PROVIDER_EXECUTION_FAILED','RESPONSE_ENVELOPE_INVALID','INCOMPLETE_OR_REFUSED_RESPONSE','RESPONSE_CONTRACT_REJECTED',
        'PROVIDER_IDENTITY_MISMATCH','DIRECTOR_OUTPUT_BUDGET_EXCEEDED'}
    for number,attempt in enumerate(call.attempts,1):
        if number>policy.maximum_attempts or success:raise ValueError('extra or unbounded annotation attempt')
        material=request_material(identity,policy,phase,subject,prompt,payload,schema,number,last)
        if (attempt.phase,attempt.subject_id,attempt.attempt,attempt.request_fingerprint)!=(phase,subject,number,fingerprint(material)):
            raise ValueError('annotation request evidence differs from actual context')
        if attempt.outcome=='VALIDATED_OUTPUT':
            if not attempt.response_fingerprint:raise ValueError('validated annotation lacks response evidence')
            success=True
        elif attempt.outcome not in allowed:raise ValueError('invalid annotation attempt outcome')
        last=attempt.outcome
    if call.failure is None:
        if not success or call.response_json is None:raise ValueError('missing complete annotation response')
    elif not allow_failure or success or call.response_json is not None:
        raise ValueError('invalid failed annotation window evidence')
    else:
        # Budget failure is possible before transport or while adding retry
        # feedback. Other failures exhaust the original bounded retry policy.
        if call.failure=='DIRECTOR_CONTEXT_BUDGET_EXCEEDED':
            try:request_material(identity,policy,phase,subject,prompt,payload,schema,len(call.attempts)+1,last)
            except ResourceLimit:pass
            else:raise ValueError('claimed context overflow does not reproduce')
        elif call.failure!=last or (len(call.attempts)!=policy.maximum_attempts and last not in
                ('PROVIDER_IDENTITY_MISMATCH','DIRECTOR_OUTPUT_BUDGET_EXCEEDED','INCOMPLETE_OR_REFUSED_RESPONSE')):
            raise ValueError('unsupported or incomplete failed annotation scope')
    return parse_json(call.response_json) if call.response_json is not None else None
