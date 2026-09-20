from .contracts import *
def select_enter_exit(ctx, *, element, event, semantically_active_after=True, reintroduced=False):
    event=tok(event,"event").lower()
    if event not in {"enter","exit"}: raise AnimationSemanticError("event must be enter/exit")
    if event=="enter" and element.visible and not reintroduced:
        return make_decision(ctx,":enter-exit",None,"UNSUPPORTED",.95,rationale=("already_visible",))
    if event=="exit" and semantically_active_after:
        return make_decision(ctx,":enter-exit",None,"BLOCKED",.98,rationale=("active_object_cannot_exit",))
    effect="introduce_semantic_object" if event=="enter" else "remove_inactive_semantic_object"
    step=AnimationStep(ctx.intent_id+":ee",event,(element.element_id,),ctx.cue.start_ms,ctx.cue.end_ms,
                       effect,element.state_id,None,{"reintroduced":reintroduced})
    return make_decision(ctx,":enter-exit",event,"PASS",.93,(step,),("semantic_lifecycle_change",),{"element_id":element.element_id})
