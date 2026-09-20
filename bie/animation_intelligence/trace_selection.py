from .contracts import *
TRACE_KINDS={"process","causal","route","graph_curve","field_line","derivation_path"}
def select_trace(ctx, *, target, trace_kind, direction_declared=True, causality_evidence=False, ordered_points=()):
    trace_kind=tok(trace_kind,"trace_kind")
    if trace_kind not in TRACE_KINDS:raise AnimationSemanticError("unsupported trace kind")
    if not direction_declared:return make_decision(ctx,":trace",None,"BLOCKED",.99,rationale=("direction_not_declared",))
    if trace_kind=="causal" and not causality_evidence:return make_decision(ctx,":trace",None,"BLOCKED",.99,rationale=("causality_evidence_required",))
    pts=tuple(ordered_points)
    if trace_kind in {"route","graph_curve","field_line"} and len(pts)<2:return make_decision(ctx,":trace",None,"REVIEW",.55,rationale=("ordered_geometry_required",))
    step=AnimationStep(ctx.intent_id+":trace","trace",(target.element_id,),ctx.cue.start_ms,ctx.cue.end_ms,
                       "trace_declared_semantic_direction",target.state_id,target.state_id,{"trace_kind":trace_kind,"points":pts})
    return make_decision(ctx,":trace","trace","PASS",.93,(step,),("direction_grounded",),{"trace_kind":trace_kind,"point_count":len(pts)})
