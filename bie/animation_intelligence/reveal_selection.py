from .contracts import *
def select_reveal(ctx, *, elements, dependency_order, progressive=True):
    es=tuple(elements); by={e.element_id:e for e in es}; order=tuple(dependency_order)
    if set(order)!=set(by) or len(order)!=len(by):
        raise AnimationSemanticError("dependency_order must cover each element exactly once")
    if progressive:
        span=ctx.cue.end_ms-ctx.cue.start_ms; steps=[]
        for i,eid in enumerate(order):
            s=ctx.cue.start_ms+span*i//len(order)
            e=ctx.cue.start_ms+span*(i+1)//len(order)
            steps.append(AnimationStep(f"{ctx.intent_id}:reveal:{i}","reveal",(eid,),s,max(s+1,e),
                                       "dependency_ordered_reveal",None,by[eid].state_id,{"index":i}))
    else:
        steps=[AnimationStep(ctx.intent_id+":reveal-all","reveal",order,ctx.cue.start_ms,ctx.cue.end_ms,"group_reveal")]
    return make_decision(ctx,":reveal","reveal","PASS",.95,steps,("dependency_order_preserved",),{"order":order,"progressive":progressive})
