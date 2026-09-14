"""BIE-DIR-HARD-LONG-DIRECTING-001: bounded windows on the same DIR execution path.

All selected decisions are planned, all generated speech is retained, and the
assembled lesson must pass the original full-scope validators and QA. Source or
continuity overflow is an explicit failure, never a summarization/truncation fix.
"""
from dataclasses import asdict, dataclass
from .context_windows import (WindowedDirectingPolicy, ContextWindow, window_view,
    build_windows, planning_contract, outline)
from .director_artifacts import array, fields, canonical, parse_json, fingerprint
from .director_model import DirectingFailure, ResourceLimit, invoke_structured, request_material
from .semantic_execution import EvaluatorIdentity
from .grounded_directing import (GroundedDirectorResult, DirectingPlan, model_context, validate_plan,
    validate_narration, NARRATION_INSTRUCTION, _schema, TEXT)
from .contextual_teaching import narration_schema, instruction_suffix


@dataclass(frozen=True)
class WindowExecution:
    policy: WindowedDirectingPolicy
    generator: EvaluatorIdentity
    windows: tuple[ContextWindow,...]
    scene_assignments: tuple[tuple[str,tuple[str,...]],...]


@dataclass(frozen=True)
class WindowedDirectorResult(GroundedDirectorResult):
    window_execution: WindowExecution


def _plan_contract(inputs,window,completed,policy):
    payload,schema,prompt=planning_contract(inputs,window,completed)
    payload['prompt_version']=policy.plan_prompt_version
    return payload,schema,prompt


def validate_window_plan(value,inputs,window,policy):
    payload,schema,prompt=_plan_contract(inputs,window,(),policy)
    fields(value,schema['required'],'window plan')
    if value['global_input_fingerprint']!=inputs.fingerprint() or value['window_fingerprint']!=window.fingerprint():
        raise ValueError('stale or substituted plan window binding')
    raw={k:v for k,v in value.items() if k not in ('global_input_fingerprint','window_fingerprint')}
    plan=validate_plan(raw,window_view(inputs,window),policy)
    if any(not s.scene_id.startswith(window.window_id+':') for s in plan.scenes):
        raise ValueError('scene ID must belong to its assigned window namespace')
    return plan


def narration_contract(inputs,window,plan,scene,narrated,policy):
    view=window_view(inputs,window); owned=set(window.decision_ids)
    local=tuple(s for s in plan.scenes if set(s.pedagogy_decision_ids) <= owned)
    by_scene={s.scene_id:s for s in plan.scenes}
    payload={'operation':'NARRATE_WINDOW','prompt_version':policy.narration_prompt_version,
        'inputs':model_context(view),'global_input_fingerprint':inputs.fingerprint(),
        'window_fingerprint':window.fingerprint(),'window':asdict(window),'global_teaching_outline':outline(inputs),
        'plan':{'input_fingerprint':view.fingerprint(),'lesson_id':plan.lesson_id,
            'scenes':[asdict(s) for s in local],'review_reasons':plan.review_reasons},
        'plan_scope':'CURRENT_WINDOW_OF_ASSEMBLED_PLAN','plan_fingerprint':plan.fingerprint(),'scene':asdict(scene),
        'completed_scene_ledger':[{'scene_id':n.scene_id,'narration_fingerprint':fingerprint(asdict(n)),
            'objective_ids':by_scene[n.scene_id].objective_ids,'pedagogy_decision_ids':by_scene[n.scene_id].pedagogy_decision_ids,
            'assessment_item_ids':[a.item_id for a in n.assessments],'review_reasons':n.review_reasons} for n in narrated],
        'prior_narration':[asdict(n) for n in narrated[-policy.prior_scene_count:]],
        'prior_narration_scope':{'kind':'COMPLETE_RECENT_SCENES_ONLY','maximum_scenes':policy.prior_scene_count,
            'all_prior_speech_retained_by_host':True,'omitted_from_request_scene_count':max(0,len(narrated)-policy.prior_scene_count)}}
    schema=_schema({**narration_schema(view)['properties'],'global_input_fingerprint':TEXT,'window_fingerprint':TEXT})
    prompt=NARRATION_INSTRUCTION+instruction_suffix(view)+'''
This scene belongs to one execution window of the assembled lesson. The current plan view is explicitly
partial; plan_fingerprint binds the complete host plan. Keep source conditions, math chains and original
assessment obligations intact. The completed_scene_ledger identifies actual earlier speech but is not
its full wording or evidence of learner mastery. prior_narration contains only complete recent scenes;
all earlier speech remains stored unchanged by BIE. Use the recent exact speech for the immediate
transition and supplied source/prerequisite definitions for conceptual continuity. Do not fabricate
earlier quotations, unseen examples, learner answers or unresolved references from a fingerprint.
Echo global_input_fingerprint and window_fingerprint as well as the view and assembled-plan bindings.'''
    return payload,schema,prompt


def validate_window_narration(value,inputs,window,plan,scene,policy):
    view=window_view(inputs,window)
    required=(*narration_schema(view)['required'],'global_input_fingerprint','window_fingerprint')
    fields(value,required,'window narration')
    if value['global_input_fingerprint']!=inputs.fingerprint() or value['window_fingerprint']!=window.fingerprint():
        raise ValueError('stale or substituted narration window binding')
    if not set(scene.pedagogy_decision_ids) <= set(window.decision_ids):
        raise ValueError('scene is outside its narrated window')
    raw={k:v for k,v in value.items() if k not in ('global_input_fingerprint','window_fingerprint')}
    return validate_narration(raw,view,plan,scene,policy)


def _invoke(provider,identity,policy,phase,subject,contract,validator,attempts):
    payload,schema,prompt=contract
    try:
        value,trace=invoke_structured(provider,identity,policy,phase,subject,prompt,payload,schema,validator)
    except DirectingFailure as failure:
        raise DirectingFailure(failure.code,tuple(attempts)+failure.attempts,failure.owner) from failure
    return value,tuple(attempts)+trace


def execute_windowed_director(inputs,generator,identity,critic,critic_identity,policy,semantic_policy):
    """Internal branch; execute_grounded_director already verified full upstream IO."""
    from .grounded_directing import _finish_director, _check_narration_budget
    try: windows=build_windows(inputs,policy,identity)
    except ResourceLimit as error:
        raise DirectingFailure('DIRECTOR_WINDOW_CONTEXT_BUDGET_EXCEEDED',owner='DIR_SCOPE') from error
    scenes=[]; assignments=[]; review=set(inputs.review_reasons); attempts=()
    for window in windows:
        local,attempts=_invoke(generator,identity,policy,'PLAN_WINDOW',window.window_id,
            _plan_contract(inputs,window,tuple(scenes),policy),
            lambda value:validate_window_plan(value,inputs,window,policy),attempts)
        scenes.extend(local.scenes); assignments.append((window.window_id,tuple(s.scene_id for s in local.scenes)))
        review.update(local.review_reasons)
    try:
        # Full original validators own final coverage/order. Window success
        # cannot weaken an original scene, prerequisite or assessment gate.
        plan=validate_plan(parse_json(canonical({'input_fingerprint':inputs.fingerprint(),'lesson_id':inputs.lesson_id,
            'scenes':[asdict(s) for s in scenes],'review_reasons':sorted(review)})),inputs,policy)
    except ResourceLimit as error:
        raise DirectingFailure('DIRECTOR_AGGREGATE_OUTPUT_BUDGET_EXCEEDED',attempts,'DIR_SCOPE') from error
    except (ValueError,TypeError,KeyError) as error:
        raise DirectingFailure('DIRECTOR_WINDOW_ASSEMBLY_INVALID',attempts,'DIR') from error
    window_by_id={w.window_id:w for w in windows}
    assigned={scene:window_by_id[wid] for wid,scene_ids in assignments for scene in scene_ids}
    narrated=[]
    for scene in plan.scenes:
        window=assigned[scene.scene_id]
        content,attempts=_invoke(generator,identity,policy,'NARRATE_WINDOW',scene.scene_id,
            narration_contract(inputs,window,plan,scene,narrated,policy),
            lambda value:validate_window_narration(value,inputs,window,plan,scene,policy),attempts)
        # Check the actual full-scope binding again before compilation.
        raw={**asdict(content),'input_fingerprint':inputs.fingerprint(),'plan_fingerprint':plan.fingerprint()}
        validate_narration(parse_json(canonical(raw)),inputs,plan,scene,policy)
        narrated.append(content); _check_narration_budget(narrated,policy,attempts)
    base=_finish_director(inputs,plan,tuple(narrated),attempts,critic,critic_identity,semantic_policy)
    return WindowedDirectorResult(**{name:getattr(base,name) for name in GroundedDirectorResult.__dataclass_fields__},
        window_execution=WindowExecution(policy,identity,windows,tuple(assignments)))


def verify_window_execution(inputs,base):
    """Reconstruct each actual window request from retained inputs and speech."""
    if not isinstance(base,WindowedDirectorResult): raise ValueError('known windowed result required')
    record=base.window_execution
    if build_windows(inputs,record.policy,record.generator)!=record.windows:
        raise ValueError('window schedule differs from the actual source/decision/policy context')
    if tuple(w.window_id for w in record.windows)!=tuple(w for w,_ in record.scene_assignments):
        raise ValueError('window coverage/ordering differs from the execution schedule')
    ordered=tuple(s for _,scenes in record.scene_assignments for s in scenes)
    if ordered!=tuple(s.scene_id for s in base.plan.scenes):
        raise ValueError('window assignment lost, duplicated or reordered a scene')
    by_scene={s.scene_id:s for s in base.plan.scenes}; attempts=base.generation_attempts; position=0
    def trace(phase,subject,contract):
        nonlocal position
        payload,schema,prompt=contract; last=None
        for number in range(1,record.policy.maximum_attempts+1):
            if position>=len(attempts): raise ValueError('missing actual window request evidence')
            attempt=attempts[position]; position+=1
            material=request_material(record.generator,record.policy,phase,subject,prompt,payload,schema,number,last)
            if (attempt.phase,attempt.subject_id,attempt.attempt,attempt.request_fingerprint)!=(phase,subject,number,fingerprint(material)):
                raise ValueError('window request evidence does not bind its source, outline, continuity or policy')
            if attempt.outcome=='VALIDATED_OUTPUT':
                if not attempt.response_fingerprint: raise ValueError('validated window lacks response evidence')
                return
            if attempt.outcome not in ('PROVIDER_EXECUTION_FAILED','RESPONSE_ENVELOPE_INVALID','INCOMPLETE_OR_REFUSED_RESPONSE','RESPONSE_CONTRACT_REJECTED'):
                raise ValueError('invalid retained window retry outcome')
            last=attempt.outcome
        raise ValueError('window evidence has no bounded successful generation')
    previous=[]
    for window,(_,scene_ids) in zip(record.windows,record.scene_assignments):
        local=tuple(by_scene[s] for s in scene_ids)
        trace('PLAN_WINDOW',window.window_id,_plan_contract(inputs,window,previous,record.policy))
        # The merged review reasons may include later windows. Coverage checks
        # are independent of those reasons and retain every original source ID.
        raw={'input_fingerprint':window.view_fingerprint,'lesson_id':inputs.lesson_id,
            'scenes':[asdict(s) for s in local],'review_reasons':[],
            'global_input_fingerprint':inputs.fingerprint(),'window_fingerprint':window.fingerprint()}
        validate_window_plan(parse_json(canonical(raw)),inputs,window,record.policy)
        previous.extend(local)
    assigned={sid:window for window,(_,scene_ids) in zip(record.windows,record.scene_assignments) for sid in scene_ids}
    previous=[]
    for scene,narration in zip(base.plan.scenes,base.narrated_scenes):
        trace('NARRATE_WINDOW',scene.scene_id,narration_contract(inputs,assigned[scene.scene_id],base.plan,scene,previous,record.policy))
        previous.append(narration)
    if position!=len(attempts): raise ValueError('unexpected extra window execution evidence')
    return record
