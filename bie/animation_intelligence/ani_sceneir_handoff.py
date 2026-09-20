from dataclasses import dataclass, field
from typing import Mapping, Any

class SceneIRHandoffError(ValueError): pass

SUPPORTED_ACTIONS={
 "enter","exit","emphasize","reveal","transform","morph","trace","path_follow",
 "camera","simulation_state","static_focus","static_trace","crossfade_states",
 "state_snapshots","progressive_static_trace","path_endpoints_with_progress_marker"
}

@dataclass(frozen=True)
class SceneIRTrack:
    node_id:str
    track_id:str
    action:str
    target_ids:tuple[str,...]
    start_ms:int
    end_ms:int
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    owner_stage:str
    parameters:Mapping[str,Any]=field(default_factory=dict)
    fallback_action:str|None=None

@dataclass(frozen=True)
class SceneIRHandoff:
    handoff_id:str
    animation_plan_fingerprint:str
    schema_version:str
    target_profile:str
    nodes:tuple[SceneIRTrack,...]
    unsupported_capabilities:tuple[str,...]
    planned_fallbacks:Mapping[str,str]
    blockers:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def build_sceneir_handoff(plan, *, sceneir_schema_version="0.1.0", capability_overrides=None):
    overrides=dict(capability_overrides or {})
    nodes=[];unsupported=[];fallbacks={};blockers=[]
    for t in plan.tracks:
        action=t.semantic_action
        effective=action
        fallback=None
        if action not in SUPPORTED_ACTIONS:
            fallback=overrides.get(action) or t.reduced_motion_variant
            if not fallback:
                unsupported.append(f"{t.track_id}:{action}")
                blockers.append(f"unsupported_action:{t.track_id}")
                continue
            if fallback not in SUPPORTED_ACTIONS:
                blockers.append(f"invalid_fallback:{t.track_id}")
                continue
            effective=fallback
            fallbacks[t.track_id]=fallback
        nodes.append(SceneIRTrack(
            node_id="ani:"+t.track_id, track_id=t.track_id, action=effective,
            target_ids=tuple(t.target_ids), start_ms=t.start_ms, end_ms=t.end_ms,
            source_refs=tuple(t.source_refs), reasoning_refs=tuple(t.reasoning_refs),
            owner_stage=t.owner_stage, parameters=dict(t.payload), fallback_action=fallback
        ))
    if not nodes:
        blockers.append("no_sceneir_nodes")
    return SceneIRHandoff(
        handoff_id="sceneir:"+plan.plan_id,
        animation_plan_fingerprint=plan.plan_fingerprint,
        schema_version=sceneir_schema_version,
        target_profile=plan.target_profile,
        nodes=tuple(nodes),
        unsupported_capabilities=tuple(sorted(unsupported)),
        planned_fallbacks=fallbacks,
        blockers=tuple(sorted(set(blockers))),
        review_required=True,
        accepted=False
    )

def require_sceneir_ready(handoff):
    if handoff.blockers:
        raise SceneIRHandoffError("Scene IR handoff blocked: "+",".join(handoff.blockers))
    if not handoff.nodes:
        raise SceneIRHandoffError("Scene IR handoff has no nodes")
    return True
