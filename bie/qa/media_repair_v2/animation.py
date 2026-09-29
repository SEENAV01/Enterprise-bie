"""Retime existing exact linear/step tracks into separately approved windows.

No endpoints, values, narration cues, motion limits or scientific conditions change.
Unsupported easing and nonintegral sample clocks require explicit upstream repair.
"""
from fractions import Fraction
from dataclasses import replace,asdict
from ..release_v2.contracts import ContractError,canonical_bytes
from ..animation_v2.models import Keyframe
from ..animation_v2.evaluator import evaluate
from ..domain_repair_v2.common import exact_inputs

def repair(r,root,p,limits,as_of):
    exact_inputs(r,root)
    if r.captures:raise ContractError('MEDIA_REPAIR_OBSERVATIONS_IMMUTABLE')
    if r.modes!=p.qa.modes or r.objects!=p.qa.objects or r.cues!=p.qa.cues:raise ContractError('MEDIA_REPAIR_ANIMATION_SCOPE')
    requirements={s.track_id:s for s in p.qa.tracks}
    if {t.track_id for t in r.tracks}!=set(requirements):raise ContractError('MEDIA_REPAIR_TRACK_SCOPE')
    windows={w.track_id:w for w in p.windows};out=[];changes=[]
    for t in r.tracks:
        spec=requirements[t.track_id]
        if (t.mode_id,t.object_id,t.property,t.semantic_id,t.purpose)!=(spec.mode_id,spec.object_id,spec.property,spec.semantic_id,spec.purpose):raise ContractError('MEDIA_REPAIR_TRACK_IDENTITY')
        if t.interpolation not in ('linear','step_end'):raise ContractError('MEDIA_REPAIR_UNSUPPORTED_EASING')
        if t.track_id not in windows:out.append(t);continue
        w=windows[t.track_id];ratio=Fraction(w.end_ms-w.start_ms,t.end_ms-t.start_ms)
        times=[w.start_ms+(k.time_ms-t.start_ms)*ratio for k in t.keyframes]
        if any(x.denominator!=1 for x in times):raise ContractError('MEDIA_REPAIR_NONINTEGRAL_KEY_CLOCK')
        new=replace(t,keyframes=tuple(Keyframe(int(time),key.value) for time,key in zip(times,t.keyframes)))
        out.append(new)
        if new!=t:changes.append(dict(track_id=t.track_id,old_start=t.start_ms,old_end=t.end_ms,new_start=new.start_ms,new_end=new.end_ms))
    after=replace(r,tracks=tuple(out));result=evaluate(after,root,p.qa,as_of=as_of)
    for area in ('temporal','motion','alignment'):
        if getattr(result,area).status=='BLOCKED':raise ContractError('MEDIA_REPAIR_ANI_POSTCHECK_BLOCKED',area)
    return canonical_bytes(asdict(after)),dict(changes=changes,unsigned_postcheck=result.to_dict(),values_and_cues_preserved=True,actual_audio_sync_verified=False,actual_playback_verified=False)
