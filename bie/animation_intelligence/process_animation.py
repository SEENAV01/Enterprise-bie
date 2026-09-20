from .biology_contracts import *
KINDS={"biological_process","cell_cycle","signaling","transport","metabolic_pathway","developmental_sequence"}
def animate_process(ctx,process_id,process_kind,states,transitions,source_ref,direction_declared=True,cyclic=False,causal_claims=False):
    if source_ref not in ctx.evidence_refs:raise BioGroundingError("source_ref not grounded")
    if process_kind not in KINDS:return plan(ctx,":process","process_animation","UNSUPPORTED",blockers=("unsupported_process_kind",))
    if not direction_declared:return plan(ctx,":process","process_animation","BLOCKED",blockers=("direction_not_declared",))
    states=tuple(states);transitions=tuple(transitions)
    if len(states)<2:raise BioTopologyError("need at least 2 states")
    sids=[tok(s["state_id"],"state_id") for s in states]
    if len(set(sids))!=len(sids):raise BioTopologyError("duplicate state")
    valid=set(sids);clean=[]
    for t in transitions:
        fr=tok(t["from"],"from");to=tok(t["to"],"to")
        if fr not in valid or to not in valid:raise BioTopologyError("unknown transition state")
        clean.append({"transition_id":tok(t["transition_id"],"transition_id"),"from":fr,"to":to,"label":t.get("label")})
    if not clean:raise BioTopologyError("transitions required")
    warnings=[]
    if causal_claims and not ctx.model_fingerprint:warnings.append("causal_process_without_bound_model")
    if cyclic and not any(t["to"]==sids[0] for t in clean):warnings.append("cycle_closure_not_explicit")
    if ctx.uncertainty>=.4:warnings.append("source_uncertainty")
    return plan(ctx,":process","process_animation","REVIEW" if warnings else "PASS",
                ops=({"op":"states","process_id":process_id,"states":states},{"op":"transitions","process_id":process_id,"transitions":clean,"cyclic":cyclic}),warnings=warnings)
