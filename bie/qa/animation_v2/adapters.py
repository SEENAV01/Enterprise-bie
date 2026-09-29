"""Pinned native compatibility diagnostics, not native score-to-acceptance promotion."""
from ...animation_intelligence.qa_contracts import Event
from ...animation_intelligence.temporal_conflict_qa import evaluate as temporal
from ...animation_intelligence.excessive_motion_qa import evaluate as motion
from ..release_v2.contracts import ContractError
from .models import AnimationRequest,AnimationPolicy

def native_diagnostics(request,policy):
    if type(request) is not AnimationRequest or type(policy) is not AnimationPolicy:raise ContractError('ANI_NATIVE_ADAPTER_TYPE')
    specs={t.track_id:t for t in policy.tracks};out=[]
    for m in policy.modes:
        events=[]
        for t in sorted(request.tracks,key=lambda x:x.track_id):
            if t.mode_id!=m.mode_id or t.track_id not in specs:continue
            s=specs[t.track_id]
            # Native motion is metadata; these values never feed the new measured motion gate.
            changes=any(a.value!=b.value for a,b in zip(t.keyframes,t.keyframes[1:]))
            events.append(Event(t.track_id,'trace',(t.object_id,),t.start_ms,t.end_ms,t.purpose,s.claim_ids,
                (t.semantic_id,),1,motion=0.5 if changes else 0,essential=s.essential))
        a=temporal(events);b=motion(events,reduced_motion_requested=m.kind=='reduced')
        out.append((m.mode_id,a.fingerprint,b.fingerprint))
    return tuple(out)
