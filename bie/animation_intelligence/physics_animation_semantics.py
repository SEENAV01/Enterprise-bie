from .physics_contracts import *
SUPPORTED={"kinematics","force","momentum","energy","field","wave","circuit","graph","particle"}
def build(ctx,semantic_type,causal_claims=()):
    if semantic_type not in SUPPORTED:return plan(ctx,":sem","physics_semantics","UNSUPPORTED",blockers=("unsupported_semantic_type",))
    warnings=[]
    if causal_claims and not ctx.model_fingerprint:warnings.append("causal_animation_requires_bound_model")
    if ctx.uncertainty>=.4:warnings.append("uncertainty_requires_review")
    return plan(ctx,":sem","physics_semantics","REVIEW" if warnings else "PASS",
                ops=({"op":"bind_semantics","semantic_type":semantic_type,"causal_claims":tuple(causal_claims)},),warnings=warnings)
