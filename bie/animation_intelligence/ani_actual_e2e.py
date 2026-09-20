from dataclasses import dataclass
from hashlib import sha256
from .vis_ani_adoption import adopt_visual_handoff
from .animation_plan_contract import AnimationTrack, AnimationPlan
from .global_timeline_solver import TrackRequest, solve
from .continuity_ledger import ContinuityLedger, ContinuityRecord
from .ani_trace_matrix import TrackTrace, audit_trace
from .ani_accessibility import AccessibilityPolicy, enforce_animation_accessibility
from .animation_performance_budget import AnimationComplexity, AnimationBudget, evaluate_budget
from .ani_sceneir_handoff import build_sceneir_handoff, require_sceneir_ready

class AniE2EError(RuntimeError): pass

@dataclass(frozen=True)
class AniE2EResult:
    run_id:str
    status:str
    visual_handoff_id:str
    animation_plan_fingerprint:str
    sceneir_handoff_id:str
    scheduled_track_ids:tuple[str,...]
    trace_passed:bool
    accessibility_status:str
    performance_action:str
    blockers:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def run_vis_to_sceneir_ready(run_id, raw_vis_handoff, *, visual_revision, narration_revision,
                             target_profile, reduced_motion_requested=False):
    blockers=[]
    adopted=adopt_visual_handoff(raw_vis_handoff, visual_revision)
    tracks=[]
    for i,p in enumerate(adopted.primitives):
        timing=adopted.timing[min(i,len(adopted.timing)-1)] if adopted.timing else {"start_ms":0,"end_ms":500}
        action=p.get("animation_action","reveal")
        reduced=p.get("reduced_motion_variant")
        tracks.append(AnimationTrack(
            track_id=p["primitive_id"], semantic_action=action,
            target_ids=(p["primitive_id"],), start_ms=int(timing["start_ms"]), end_ms=int(timing["end_ms"]),
            source_refs=tuple(p["source_refs"]), reasoning_refs=tuple(p["reasoning_refs"]),
            owner_stage=p.get("owner_stage","SEM"), reduced_motion_variant=reduced, payload=dict(p.get("payload",{}))
        ))
    if not tracks:
        raise AniE2EError("VIS handoff produced no animation tracks")
    scene_start=min(t.start_ms for t in tracks); scene_end=max(t.end_ms for t in tracks)
    plan=AnimationPlan(
        plan_id="ani:"+run_id, schema_version="1.0.0", visual_handoff_id=adopted.handoff_id,
        visual_plan_fingerprint=adopted.plan_fingerprint, visual_revision=visual_revision,
        narration_revision=narration_revision, target_profile=target_profile, tracks=tuple(tracks),
        scene_start_ms=scene_start, scene_end_ms=scene_end,
        source_refs=tuple(sorted({x for t in tracks for x in t.source_refs})),
        reasoning_refs=tuple(sorted({x for t in tracks for x in t.reasoning_refs})),
        reduced_motion_requested=reduced_motion_requested
    )
    reqs=[TrackRequest(t.track_id,t.start_ms,t.end_ms-t.start_ms,t.start_ms,t.end_ms,1.0,None,True) for t in tracks]
    timeline=solve(reqs)
    if not timeline.solved:
        blockers.append("timeline_unsat")
    access=enforce_animation_accessibility(tracks, AccessibilityPolicy(reduced_motion_requested))
    if access.status=="BLOCKED":
        blockers.append("accessibility_blocked")
    perf=evaluate_budget(
        AnimationComplexity(tuple(t.track_id for t in tracks),len(tracks),1,0,0,0,
                            sum(1 for t in tracks if t.semantic_action=="camera"),0),
        AnimationBudget(target_profile,20,35,1000,4,10_000_000)
    )
    trace=audit_trace([
        TrackTrace(t.track_id,t.source_refs,t.reasoning_refs,t.target_ids,t.owner_stage,("ani-e2e",),
                   ("ani:"+t.track_id,),True) for t in tracks
    ])
    if not trace.passed:
        blockers.append("trace_blocked")
    ledger=ContinuityLedger()
    for t in tracks:
        ledger.add(ContinuityRecord("scene-1",t.target_ids[0],t.target_ids[0],"visual",None,None,None,None,None))
    handoff=build_sceneir_handoff(plan)
    if handoff.blockers:
        blockers.append("sceneir_handoff_blocked")
    if not blockers:
        require_sceneir_ready(handoff)
    return AniE2EResult(
        run_id, "BLOCKED" if blockers else "PASS", adopted.handoff_id, plan.plan_fingerprint,
        handoff.handoff_id, tuple(x.track_id for x in timeline.scheduled), trace.passed,
        access.status, perf.action, tuple(sorted(set(blockers))), True, False
    )
