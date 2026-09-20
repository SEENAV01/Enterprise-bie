from .math_contracts import *

def animate_derivation(ctx, *, derivation_id, steps, source_ref,
                       dependency_edges=(), reveal_mode="stepwise",
                       preserve_side_conditions=True):
    derivation_id=tok(derivation_id,"derivation_id")
    if source_ref not in ctx.evidence_refs:
        raise MathGroundingError("derivation source_ref not grounded")
    if reveal_mode not in {"stepwise","paired","progressive"}:
        raise MathAnimationError("unsupported reveal_mode")
    steps=tuple(steps)
    if len(steps)<2:
        raise MathAnimationError("derivation needs at least two steps")
    clean=[]
    seen=set()
    for s in steps:
        sid=tok(s.get("step_id"),"step_id")
        if sid in seen: raise MathAnimationError("duplicate derivation step")
        seen.add(sid)
        expr=tok(s.get("expression"),"expression")
        justification=tok(s.get("justification"),"justification")
        side=tuple(tok(x,"side_condition") for x in s.get("side_conditions",()))
        clean.append({"step_id":sid,"expression":expr,"justification":justification,"side_conditions":side})
    valid=set(seen); edges=[]
    indeg={x:0 for x in valid}; adj={x:[] for x in valid}
    for e in dependency_edges:
        a=tok(e.get("before"),"before");b=tok(e.get("after"),"after")
        if a not in valid or b not in valid: raise MathAnimationError("dependency edge references unknown step")
        if a==b: raise MathAnimationError("self dependency invalid")
        edges.append((a,b));adj[a].append(b);indeg[b]+=1
    base={s["step_id"]:i for i,s in enumerate(clean)}
    ready=sorted([x for x,d in indeg.items() if d==0],key=lambda x:base[x]);order=[]
    while ready:
        x=ready.pop(0);order.append(x)
        for y in adj[x]:
            indeg[y]-=1
            if indeg[y]==0:
                ready.append(y);ready.sort(key=lambda z:base[z])
    if len(order)!=len(clean):
        return make_plan(ctx,suffix=":derivation",kind="derivation_animation",status="BLOCKED",
                         blockers=("derivation_dependency_cycle",))
    warnings=[]
    if any(s["side_conditions"] for s in clean) and not preserve_side_conditions:
        return make_plan(ctx,suffix=":derivation",kind="derivation_animation",status="BLOCKED",
                         blockers=("side_conditions_cannot_be_dropped",))
    if ctx.uncertainty>=.4: warnings.append("source_uncertainty_requires_review")
    ops=(
        {"op":"materialize_derivation","derivation_id":derivation_id,"steps":clean,"reveal_mode":reveal_mode},
        {"op":"animate_derivation_order","derivation_id":derivation_id,"step_order":order,
         "dependency_edges":edges,"preserve_side_conditions":bool(preserve_side_conditions)}
    )
    return make_plan(ctx,suffix=":derivation",kind="derivation_animation",
                     status="REVIEW" if warnings else "PASS",operations=ops,warnings=warnings)
