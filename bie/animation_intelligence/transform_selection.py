from .contracts import *
def select_transform(ctx, *, source, target, relation, identity_preserved=True, semantic_invariants=()):
    relation=tok(relation,"relation");inv=tuple(tok(x,"semantic_invariant") for x in semantic_invariants)
    if identity_preserved and (source.identity_id or source.element_id)!=(target.identity_id or target.element_id):
        return make_decision(ctx,":transform",None,"BLOCKED",.98,rationale=("identity_mismatch",))
    if source.geometry_kind!=target.geometry_kind and not ctx.payload.get("geometry_conversion_allowed",False):
        return make_decision(ctx,":transform",None,"REVIEW",.58,rationale=("geometry_conversion_requires_explicit_semantics",))
    step=AnimationStep(ctx.intent_id+":transform","transform",(source.element_id,target.element_id),
                       ctx.cue.start_ms,ctx.cue.end_ms,"declared_state_transform",
                       source.state_id,target.state_id,{"relation":relation,"invariants":inv})
    return make_decision(ctx,":transform","transform","PASS",.92,(step,),("states_explicitly_related",),{"relation":relation,"invariants":inv})
