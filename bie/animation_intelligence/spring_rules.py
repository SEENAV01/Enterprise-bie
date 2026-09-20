from .easing_contracts import *
from math import sqrt, exp, pi

def configure_spring(ctx, *, stiffness=170.0, damping=26.0, mass=1.0,
                     initial_velocity=0.0, overshoot_allowed=False,
                     represents_physical_motion=False, physical_model_verified=False):
    k=finite(stiffness,"stiffness");c=finite(damping,"damping");m=finite(mass,"mass");v=finite(initial_velocity,"initial_velocity")
    if k<=0 or c<0 or m<=0:
        raise SpringRuleError("spring parameters out of range")
    blockers=[];warnings=[]
    if represents_physical_motion and not physical_model_verified:
        blockers.append("ui_spring_cannot_claim_physical_dynamics_without_verified_model")
    zeta=c/(2*sqrt(k*m))
    omega_n=sqrt(k/m)
    settling_ms=round(4000/(zeta*omega_n)) if zeta>0 else 10_000
    if zeta<1:
        overshoot=exp((-zeta*pi)/sqrt(max(1e-12,1-zeta*zeta)))
    else:
        overshoot=0.0
    if overshoot>0.02 and not overshoot_allowed:
        warnings.append("spring_overshoot_exceeds_semantic_policy")
    if ctx.semantic_action in {"trace","path_follow","simulation_state"}:
        warnings.append("spring_not_preferred_for_rate_sensitive_semantics")
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return make_policy(ctx,suffix=":spring",status=status,easing="spring",duration_ms=max(1,settling_ms),
                       parameters={"stiffness":k,"damping":c,"mass":m,"initial_velocity":v,
                                   "damping_ratio":round(zeta,6),"natural_frequency":round(omega_n,6),
                                   "estimated_overshoot_ratio":round(overshoot,6),
                                   "overshoot_allowed":bool(overshoot_allowed),
                                   "represents_physical_motion":bool(represents_physical_motion),
                                   "physical_model_verified":bool(physical_model_verified)},
                       warnings=warnings,blockers=blockers)
