from .contracts import *
def select_path_follow(ctx, *, element, path_id, ordered_points, path_semantics, actual_trajectory=False, illustrative_only=False):
    path_id=tok(path_id,"path_id");path_semantics=tok(path_semantics,"path_semantics");pts=tuple(ordered_points)
    if len(pts)<2:return make_decision(ctx,":path",None,"BLOCKED",.99,rationale=("path_geometry_required",))
    if actual_trajectory and illustrative_only:return make_decision(ctx,":path",None,"BLOCKED",.99,rationale=("illustrative_path_cannot_claim_trajectory",))
    if actual_trajectory and not element.payload.get("trajectory_evidence",False):return make_decision(ctx,":path",None,"REVIEW",.50,rationale=("trajectory_evidence_required",))
    step=AnimationStep(ctx.intent_id+":path","path_follow",(element.element_id,),ctx.cue.start_ms,ctx.cue.end_ms,
                       "follow_declared_semantic_path",element.state_id,element.state_id,
                       {"path_id":path_id,"points":pts,"path_semantics":path_semantics,"actual_trajectory":actual_trajectory})
    return make_decision(ctx,":path","path_follow","PASS",.90,(step,),("path_semantics_explicit",),{"path_id":path_id,"point_count":len(pts)})
