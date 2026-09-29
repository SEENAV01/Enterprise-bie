"""Text-bound conservative scene reflow. Does not invent a hook, payoff or narration.

Equal-start narration/text remain co-presented. Ambiguous overlapping speech is
escalated. Existing gaps/pauses and content inventories are never shortened.
"""
from dataclasses import replace
from fractions import Fraction
from ..release_v2.contracts import ContractError
from ..director_v2.models import DirectorRequest,DirectorPolicy
from ..director_v2.metrics import merged_text,codepoints,needs_expanded_readout
from .contracts import Limits
from .common import exact_inputs,finish

def repair(request,root,policy,limits=Limits()):
    if type(request) is not DirectorRequest or type(policy) is not DirectorPolicy:raise ContractError('DOMAIN_REPAIR_DIRECTOR_TYPE')
    exact_inputs(request,root)
    if (request.lesson_id,request.audience_id,request.language)!=(policy.lesson_id,policy.audience_id,policy.language):raise ContractError('DOMAIN_REPAIR_DIRECTOR_IDENTITY')
    if {s.scene_id for s in request.scenes}!={s.scene_id for s in policy.scenes}:raise ContractError('DOMAIN_REPAIR_SCENE_SCOPE')
    claims={c.claim_id:c for c in request.source.claims};forms={f.beat_id:f for f in request.spoken_forms}
    if any(f.beat_id not in {b.beat_id for b in request.beats} for f in request.spoken_forms):raise ContractError('DOMAIN_REPAIR_SPOKEN_FORM_REFERENCE')
    updates={};scenes=[];changed=[];added=0
    for scene in request.scenes:
        beats=sorted((b for b in request.beats if b.scene_id==scene.scene_id),key=lambda b:(b.start_ms,b.beat_id))
        if not beats:raise ContractError('DOMAIN_REPAIR_EMPTY_SCENE')
        groups=[]
        for beat in beats:
            if not groups or groups[-1][0].start_ms!=beat.start_ms:groups.append([])
            groups[-1].append(beat)
        shift=0;previous_old_end=0;previous_new_end=0
        for group in groups:
            old_start=group[0].start_ms
            if old_start<previous_old_end:raise ContractError('DOMAIN_REPAIR_OVERLAP_REDESIGN_REQUIRED')
            if sum(b.channel in ('narration','dialogue') for b in group)>1:raise ContractError('DOMAIN_REPAIR_AMBIGUOUS_SPEAKERS')
            minimum={}
            for b in group:
                if any(c not in claims for c in b.claim_ids):raise ContractError('DOMAIN_REPAIR_BEAT_CLAIM')
                text=merged_text(claims,b.claim_ids) if b.claim_ids else ''
                count=codepoints(text);form=forms.get(b.beat_id)
                if b.channel in ('narration','dialogue') and needs_expanded_readout(text) and form is None:raise ContractError('DOMAIN_REPAIR_EXPANDED_SPEECH_REQUIRED')
                if form is not None:
                    if not form.claim_ids or any(c not in claims for c in form.claim_ids):raise ContractError('DOMAIN_REPAIR_SPOKEN_FORM_UNGROUNDED')
                    spoken=merged_text(claims,form.claim_ids)
                    if form.text!=spoken:raise ContractError('DOMAIN_REPAIR_SPOKEN_FORM_MISMATCH')
                    count=max(count,codepoints(spoken))
                rate=policy.pacing.speech_codepoints_per_minute if b.channel in ('narration','dialogue') else policy.pacing.screen_codepoints_per_minute
                required=(count*60000+rate-1)//rate if b.channel!='pause' else 0
                minimum[b.beat_id]=max(b.end_ms-b.start_ms,required)
            extension=max(minimum[b.beat_id]-(b.end_ms-b.start_ms) for b in group)
            new_start=old_start+shift
            for b in group:
                new=replace(b,start_ms=new_start,end_ms=new_start+(b.end_ms-b.start_ms)+extension)
                updates[b.beat_id]=new
                if new!=b:changed.append(b.beat_id)
            previous_old_end=max(b.end_ms for b in group)
            previous_new_end=max(updates[b.beat_id].end_ms for b in group)
            shift+=extension
        duration=max(scene.duration_ms+shift,previous_new_end)
        added+=duration-scene.duration_ms;scenes.append(replace(scene,duration_ms=duration))
    if set(updates)!={b.beat_id for b in request.beats}:raise ContractError('DOMAIN_REPAIR_UNKNOWN_SCENE')
    if added>limits.max_added_ms:raise ContractError('DOMAIN_REPAIR_TIME_BUDGET')
    expected={r.route_id:r for r in policy.routes};durations={s.scene_id:s.duration_ms for s in scenes}
    if set(expected)!={r.route_id for r in request.routes}:raise ContractError('DOMAIN_REPAIR_ROUTE_SCOPE')
    for route in request.routes:
        spec=expected[route.route_id]
        if set(route.scene_ids)!=set(spec.scene_ids):raise ContractError('DOMAIN_REPAIR_ROUTE_MEMBERSHIP')
        offsets={};cursor=0
        for sid in route.scene_ids:offsets[sid]=cursor;cursor+=durations[sid]
        if cursor>spec.max_duration_ms:raise ContractError('DOMAIN_REPAIR_ROUTE_DURATION')
        for c in policy.timing_constraints:
            a=updates.get(c.before_beat_id);b=updates.get(c.after_beat_id)
            if a is None or b is None:raise ContractError('DOMAIN_REPAIR_TIMING_REFERENCE')
            if a.scene_id in offsets and b.scene_id in offsets:
                gap=offsets[b.scene_id]+b.start_ms-offsets[a.scene_id]-a.end_ms
                if not c.minimum_gap_ms<=gap<=c.maximum_gap_ms:raise ContractError('DOMAIN_REPAIR_TIMING_CONSTRAINT')
    after=replace(request,scenes=tuple(scenes),beats=tuple(updates[b.beat_id] for b in request.beats))
    return finish(request,after,dict(worker='text-bound-conservative-scene-reflow',changed_beat_ids=changed,
        added_duration_ms=added,narration_changed=False,source_conditions_changed=False,
        pauses_shortened=False,measured_audio_timing=False),limits)
