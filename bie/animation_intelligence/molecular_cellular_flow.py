from .biology_contracts import *
KINDS={"cell","organelle","membrane","molecule","tissue","extracellular_space","channel","receptor"}
def animate_flow(ctx,flow_id,compartments,transfers,source_ref,direction_declared=True,concentration_claims=False,permeability_claims=False,model_generated=False):
    if source_ref not in ctx.evidence_refs:raise BioGroundingError("source_ref not grounded")
    if not direction_declared:return plan(ctx,":flow","molecular_cellular_flow","BLOCKED",blockers=("direction_not_declared",))
    compartments=tuple(compartments);transfers=tuple(transfers)
    if len(compartments)<2:raise BioTopologyError("need at least 2 compartments")
    seen=set();cc=[]
    for c in compartments:
        cid=tok(c["compartment_id"],"compartment_id");kind=tok(c["kind"],"kind")
        if cid in seen:raise BioTopologyError("duplicate compartment")
        if kind not in KINDS:raise BioTopologyError("unsupported compartment")
        seen.add(cid);cc.append({"compartment_id":cid,"kind":kind,"label":c.get("label")})
    tt=[]
    for t in transfers:
        fr=tok(t["from"],"from");to=tok(t["to"],"to")
        if fr not in seen or to not in seen:raise BioTopologyError("unknown compartment")
        amount=t.get("amount")
        if amount is not None:amount=finite(amount,"amount")
        tt.append({"transfer_id":tok(t["transfer_id"],"transfer_id"),"from":fr,"to":to,"molecule":tok(t["molecule"],"molecule"),"amount":amount,"unit":t.get("unit")})
    if not tt:raise BioTopologyError("transfers required")
    if model_generated and not ctx.model_fingerprint:return plan(ctx,":flow","molecular_cellular_flow","BLOCKED",blockers=("model_fingerprint_required",))
    warnings=[]
    if concentration_claims and not any(t["amount"] is not None for t in tt):warnings.append("concentration_claim_without_quantitative_data")
    if permeability_claims and not any(c["kind"] in {"membrane","channel"} for c in cc):warnings.append("permeability_claim_without_membrane_or_channel")
    if ctx.uncertainty>=.4:warnings.append("source_uncertainty")
    return plan(ctx,":flow","molecular_cellular_flow","REVIEW" if warnings else "PASS",
                ops=({"op":"compartments","flow_id":flow_id,"compartments":cc},{"op":"transfers","flow_id":flow_id,"transfers":tt,"model_generated":model_generated}),warnings=warnings)
