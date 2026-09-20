from dataclasses import dataclass

class EconomicsAnimationError(ValueError): pass

@dataclass(frozen=True)
class Curve:
    curve_id:str
    role:str
    points:tuple[tuple[float,float],...]
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]

@dataclass(frozen=True)
class EconomicsPlan:
    plan_id:str
    status:str
    operations:tuple[dict,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def _check_curve(c):
    if c.role not in {"demand","supply","ad","as","is","lm","budget","ppf","custom"}:
        raise EconomicsAnimationError("unsupported curve role")
    if len(c.points)<2 or not c.source_refs or not c.reasoning_refs:
        raise EconomicsAnimationError("curve points/lineage required")

def plan_curve_shift(plan_id,base_curve,target_curve,*,driver,claim_type="comparative_statics",
                     equilibrium_before=None,equilibrium_after=None):
    _check_curve(base_curve);_check_curve(target_curve)
    if base_curve.role!=target_curve.role:
        raise EconomicsAnimationError("curve role changed without explicit model")
    if claim_type not in {"comparative_statics","illustrative","empirical"}:
        raise EconomicsAnimationError("unsupported claim_type")
    blockers=[];warnings=[]
    if not driver: blockers.append("economic_driver_required")
    if claim_type=="empirical" and not (base_curve.source_refs and target_curve.source_refs):
        blockers.append("empirical_shift_requires_sources")
    if (equilibrium_before is None)!=(equilibrium_after is None):
        warnings.append("incomplete_equilibrium_comparison")
    ops=(
      {"op":"draw_base_curve","curve":base_curve.__dict__},
      {"op":"animate_curve_shift","from":base_curve.points,"to":target_curve.points,"driver":driver,"claim_type":claim_type},
    )
    if equilibrium_before is not None and equilibrium_after is not None:
        ops += ({"op":"animate_equilibrium_change","before":equilibrium_before,"after":equilibrium_after},)
    return EconomicsPlan(plan_id,"BLOCKED" if blockers else ("REVIEW" if warnings else "PASS"),
                         ops,tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),True,False)

def plan_circular_flow(plan_id,nodes,flows,*,source_refs,reasoning_refs):
    nodes=tuple(nodes);flows=tuple(flows)
    if len(nodes)<2 or not flows: raise EconomicsAnimationError("nodes/flows required")
    if not source_refs or not reasoning_refs: raise EconomicsAnimationError("lineage required")
    valid=set(nodes);blockers=[]
    for f in flows:
        if f["from"] not in valid or f["to"] not in valid: blockers.append("unknown_flow_node")
        if not f.get("label"): blockers.append("unlabeled_flow")
    ops=({"op":"materialize_economic_nodes","nodes":nodes},
         {"op":"animate_economic_flows","flows":flows})
    return EconomicsPlan(plan_id,"BLOCKED" if blockers else "PASS",ops,
                         tuple(sorted(set(blockers))),(),True,False)
