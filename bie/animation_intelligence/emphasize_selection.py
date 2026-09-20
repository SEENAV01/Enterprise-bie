from .contracts import *
def select_emphasis(ctx, *, element, reason, quantitative_semantics=False, allow_scale_emphasis=False, competing_focus=False):
    reason=tok(reason,"reason")
    if competing_focus:
        return make_decision(ctx,":emphasis",None,"REVIEW",.55,rationale=("competing_focus_detected",))
    mode="highlight" if element.semantic_role in {"text","label","equation"} else "accent"
    scale_allowed=bool(allow_scale_emphasis or not quantitative_semantics)
    step=AnimationStep(ctx.intent_id+":emphasis","emphasize",(element.element_id,),ctx.cue.start_ms,ctx.cue.end_ms,
                       "increase_attention_without_changing_semantic_value",element.state_id,element.state_id,
                       {"mode":mode,"reason":reason,"scale_allowed":scale_allowed})
    return make_decision(ctx,":emphasis","emphasize","PASS",.94,(step,),("attention_only",),{"mode":mode,"scale_allowed":scale_allowed})
