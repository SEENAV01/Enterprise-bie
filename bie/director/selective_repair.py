"""BIE-DIR-HARD-REPAIR-001: bounded phase repair from actual completed evidence.

Reuses exact plan/narration only when their complete inputs, generation policy,
generator and code match. Named-scene correction recompiles and rechecks the
whole lesson; unchanged scene-local annotations may be reused only under the
hierarchical policy while every global discourse/review scope executes again.
"""
from dataclasses import asdict, replace
from .director_artifacts import fields, fingerprint
from .director_model import DirectingFailure
from .grounded_directing import code_fingerprint
from .narration_annotations import verify_base
from .recovery_codec import grounded_record
from .semantic_execution import evaluate_script_semantics
from .script_coherence_qa import coherence_qa
from .repetition_detection import repetition_qa
from .age_level_qa import age_level_qa
from .pacing_qa import pacing_qa
from bie.infrastructure.orchestrator import StageExecutionFailure


def prepare_repair(executor, context, inputs, previous_revision=None):
    request = context.configuration.get('director_repair')
    if request is None:
        return None, (), None
    expected=('previous_idempotency_key',)+(('scene_corrections',) if 'scene_corrections' in request else ())
    fields(request, expected, 'director repair')
    previous_key = request['previous_idempotency_key']
    if not isinstance(previous_key, str) or not previous_key.strip() or previous_key == context.idempotency_key or context.attempt < 2:
        raise DirectingFailure('DIRECTOR_REPAIR_ATTEMPT_INVALID', owner='DIR_REPAIR')
    prior = executor.idempotency.get(previous_key)
    if previous_revision is not None and previous_revision.execution_fingerprint != prior.fingerprint:
        raise DirectingFailure('DIRECTOR_REPAIR_REQUIRES_PREVIOUS_REVISION', owner='DIR_REPAIR')
    if prior.state != 'COMPLETED':
        raise DirectingFailure('DIRECTOR_REPAIR_REQUIRES_COMPLETED_ATTEMPT', owner='INFRA')
    # Reuse existing replay verification for all CAS/envelope parent bytes.
    try:
        executor._replay(prior.result_ref, prior.fingerprint)
    except StageExecutionFailure:
        pass
    record = executor._read_blob(prior.result_ref)
    evidence_ids = [r for r in record['value']['evidence_refs'] if not r.startswith('cas:')]
    evidence = [executor.io.load(r) for r in evidence_ids]
    if any(a.run_id != context.run_id for a in evidence):
        raise DirectingFailure('DIRECTOR_REPAIR_CROSS_RUN', owner='DIR_REPAIR')
    candidates = [];prior_annotation_raw=None
    for artifact in evidence:
        if (artifact.artifact_type in ('evidence.director_base_execution', 'evidence.director_execution')
                and artifact.metadata.get('execution_fingerprint') != prior.fingerprint):
            raise ValueError('repair evidence belongs to a different execution')
        payload = artifact.payload
        if artifact.artifact_type == 'evidence.director_base_execution':
            candidates.append((artifact, payload['result']))
        elif artifact.artifact_type == 'evidence.director_execution':
            raw = payload['result']
            candidates.append((artifact, raw.get('base_result', raw)))
            if 'annotation_production' in raw:prior_annotation_raw=raw['annotation_production']
        if 'result' in payload and fingerprint(payload['result']) != payload['result_fingerprint']:
            raise ValueError('retained result fingerprint mismatch')
    reused = None
    reason = 'NO_COMPLETE_NARRATION_CHECKPOINT'
    if candidates:
        artifact, raw = candidates[0]
        if raw['plan']['lesson_id'] != inputs.lesson_id:
            raise DirectingFailure('DIRECTOR_REPAIR_CROSS_LESSON', owner='DIR_REPAIR')
        dependencies = {'INPUTS': raw['input_fingerprint'] == inputs.fingerprint(),
                        'CODE': raw['code_fingerprint'] == code_fingerprint(),
                        'GENERATOR': artifact.payload['generator'] == asdict(executor.generator_identity),
                        'GENERATION_POLICY': artifact.payload['policy'] == asdict(executor.policy)}
        changed = tuple(k for k, same in dependencies.items() if not same)
        reason = 'CHANGED_' + '_'.join(changed) if changed else 'EXACT_GENERATION_DEPENDENCIES_RETAINED'
        if not changed:
            base = grounded_record(raw)
            verify_base(executor.io, inputs, base)
            semantic = evaluate_script_semantics(base.execution.snapshot, base.execution.claims, inputs.catalog, inputs.sources,
                executor.critic, executor.critic_identity, executor.semantic_policy)
            e = base.execution
            qa = (coherence_qa(e.snapshot, e.architecture, ()), repetition_qa(e.snapshot), age_level_qa(e.snapshot),
                  pacing_qa(e.snapshot, e.speech, e.pauses, e.emphasis, e.timeline))
            reused = replace(base, semantic_evaluation=semantic, qa_reports=qa)
    else:
        # An operational failure without a source lineage must still bind this run.
        failures = [executor._read_blob(r) for r in record['value']['evidence_refs'] if r.startswith('cas:')]
        if not failures or any(r.get('run_id') != context.run_id or r.get('stage_id') != 'DIRECTOR' for r in failures):
            raise ValueError('unbound operational recovery')
    annotation_reuse=None;corrected=()
    corrections=request.get('scene_corrections',[])
    if corrections:
        if reused is None:raise DirectingFailure('DIRECTOR_SCENE_CORRECTION_REQUIRES_EXACT_BASE',owner='DIR_REPAIR')
        if type(corrections) is not list or not corrections:raise DirectingFailure('DIRECTOR_SCENE_CORRECTION_INVALID',owner='DIR_REPAIR')
        scene_ids=[];reasons={}
        for row in corrections:
            fields(row,('scene_id','reasons'),'scene correction request')
            scene=row['scene_id'];reason_values=tuple(row['reasons']) if type(row['reasons']) is list else ()
            if not isinstance(scene,str) or not scene.strip() or not reason_values:raise DirectingFailure('DIRECTOR_SCENE_CORRECTION_INVALID',owner='DIR_REPAIR')
            scene_ids.append(scene);reasons[scene]=reason_values
        from .scene_correction import correct_scenes,SceneCorrectionPolicy
        reused=correct_scenes(executor.io,inputs,reused,executor.generator,executor.generator_identity,
            executor.critic,executor.critic_identity,executor.semantic_policy,tuple(scene_ids),reasons,SceneCorrectionPolicy())
        corrected=tuple(scene_ids)
        if executor.annotations is not None:
            from .hierarchical_annotations import HierarchicalAnnotationPolicy
            if not isinstance(executor.annotations.policy,HierarchicalAnnotationPolicy) or prior_annotation_raw is None:
                raise DirectingFailure('DIRECTOR_SCENE_CORRECTION_REUSE_POLICY_REQUIRED',owner='DIR_ANNOTATIONS')
            from .recovery_codec import annotation_production_record
            annotation_reuse=(annotation_production_record(prior_annotation_raw),reused.original_result)
    parents = inputs.parent_refs + tuple(a.to_ref() for a in evidence if a.to_ref() not in inputs.parent_refs)
    receipt = executor.io.derive('evidence.director_repair', context.run_id, parents,
        {'schema_version': 'bie.dir.phase_repair/1.0.0', 'previous_idempotency_key': previous_key,
         'previous_execution_fingerprint': prior.fingerprint, 'attempt': context.attempt,
         'input_fingerprint': inputs.fingerprint(), 'reason': reason,
         'action': 'CORRECT_NAMED_SCENES_REUSE_OTHERS_RECHECK_ALL' if corrected else ('REUSE_PLAN_NARRATION_RECHECK_QA' if reused else 'REGENERATE'),
         'corrected_scene_ids': list(corrected),'annotation_local_reuse_candidate': bool(annotation_reuse),
         'reused_phases': ['PLAN', 'UNCHANGED_SCENES'] if corrected else (['PLAN', 'NARRATE', 'COMPILE'] if reused else []),
         'required_phases': ([] if reused else ['PLAN', 'NARRATE', 'COMPILE']) + ['FACTUAL_QA'] +
            (['ANNOTATE', 'ANNOTATION_REVIEW', 'FINE_FACTUAL_QA', 'COMPOSE_QA_TIMING'] if executor.annotations is not None else []),
         'accepted': False}, stage_id='DIRECTOR', metadata={'requires_review': True, 'accepted': False}, evidence=True)
    return reused, (receipt,), annotation_reuse
