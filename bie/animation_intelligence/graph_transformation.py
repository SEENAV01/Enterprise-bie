from .math_contracts import *

ALLOWED={"translation","scaling","reflection","rotation","parameter_change","domain_restriction","composition"}

def animate_graph_transformation(ctx, *, graph_id, source_function, target_function,
                                 transform_kind, parameters, source_ref,
                                 domain=None, preserve_asymptotes=False,
                                 equivalence_claim="transformation"):
    graph_id=tok(graph_id,"graph_id")
    source_function=tok(source_function,"source_function")
    target_function=tok(target_function,"target_function")
    if source_ref not in ctx.evidence_refs:
        raise MathGroundingError("graph transform source_ref not grounded")
    if transform_kind not in ALLOWED:
        raise MathAnimationError("unsupported transform_kind")
    if equivalence_claim not in {"transformation","equivalent_graph","illustrative"}:
        raise MathAnimationError("unsupported equivalence_claim")
    params=canonical(dict(parameters or {}))
    blockers=[];warnings=[]
    if transform_kind in {"translation","scaling","rotation","parameter_change"} and not params:
        blockers.append("transform_parameters_required")
    if domain is not None:
        lo,hi=finite(domain[0],"domain lower"),finite(domain[1],"domain upper")
        if hi<=lo: raise MathDomainError("invalid domain")
        domain=(lo,hi)
    if equivalence_claim=="equivalent_graph" and transform_kind not in {"translation","scaling","reflection","rotation","composition"}:
        warnings.append("equivalent_graph_claim_requires_mathematical_verification")
    if preserve_asymptotes and not ctx.payload.get("asymptote_evidence",False):
        warnings.append("asymptote_preservation_requires_explicit_evidence")
    ops=(
        {"op":"graph_transform","graph_id":graph_id,"source_function":source_function,
         "target_function":target_function,"transform_kind":transform_kind,"parameters":params,
         "domain":domain,"preserve_asymptotes":bool(preserve_asymptotes),
         "equivalence_claim":equivalence_claim},
    )
    status="BLOCKED" if blockers else ("REVIEW" if warnings or ctx.uncertainty>=.4 else "PASS")
    return make_plan(ctx,suffix=":graph-transform",kind="graph_transformation",
                     status=status,operations=ops,warnings=warnings,blockers=blockers)
