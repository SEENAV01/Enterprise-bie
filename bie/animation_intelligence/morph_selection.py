from .contracts import *
def select_morph(ctx, *, source, target, correspondence, morph_kind="shape", semantic_equivalence=False):
    corr=dict(correspondence or {})
    if not corr:return make_decision(ctx,":morph",None,"BLOCKED",.99,rationale=("explicit_correspondence_required",))
    if len(set(corr.values()))!=len(corr):return make_decision(ctx,":morph",None,"BLOCKED",.99,rationale=("correspondence_not_one_to_one",))
    if morph_kind not in {"shape","diagram","equation"}:raise AnimationSemanticError("unsupported morph kind")
    if morph_kind=="equation" and not semantic_equivalence:return make_decision(ctx,":morph",None,"BLOCKED",.99,rationale=("equation_equivalence_required",))
    step=AnimationStep(ctx.intent_id+":morph","morph",(source.element_id,target.element_id),ctx.cue.start_ms,ctx.cue.end_ms,
                       "map_explicit_corresponding_semantic_parts",source.state_id,target.state_id,{"morph_kind":morph_kind,"correspondence":corr})
    return make_decision(ctx,":morph","morph","PASS",.90,(step,),("explicit_correspondence",),{"morph_kind":morph_kind,"correspondence":corr})
