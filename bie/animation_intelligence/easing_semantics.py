from .easing_contracts import *

SEMANTIC_EASING={
    "enter":"ease_out",
    "exit":"ease_in",
    "emphasize":"ease_in_out",
    "reveal":"ease_out",
    "transform":"ease_in_out",
    "morph":"ease_in_out",
    "trace":"linear",
    "path_follow":"linear",
    "camera":"ease_in_out",
    "simulation_state":"linear",
}

def select_easing_semantics(ctx, *, continuity_required=False, constant_rate_semantics=False,
                            abrupt_state_change=False, requested_easing=None):
    action=ctx.semantic_action
    if action not in SEMANTIC_EASING:
        return make_policy(ctx,suffix=":easing",status="UNSUPPORTED",easing="linear",
                           blockers=("unsupported_semantic_action",))
    warnings=[]; blockers=[]
    easing=SEMANTIC_EASING[action]
    if constant_rate_semantics:
        easing="linear"
    if abrupt_state_change:
        easing="step"
    if requested_easing is not None:
        requested_easing=tok(requested_easing,"requested_easing")
        allowed={"linear","ease_in","ease_out","ease_in_out","step","spring"}
        if requested_easing not in allowed:
            raise EasingError("unsupported requested_easing")
        if constant_rate_semantics and requested_easing!="linear":
            blockers.append("constant_rate_semantics_require_linear_easing")
        elif abrupt_state_change and requested_easing!="step":
            blockers.append("abrupt_state_change_requires_step_easing")
        else:
            easing=requested_easing
    if continuity_required and easing=="step":
        blockers.append("continuity_required_but_step_easing_selected")
    if easing=="spring" and action in {"trace","path_follow","simulation_state"}:
        warnings.append("spring_may_distort_rate_or_state_semantics")
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return make_policy(ctx,suffix=":easing",status=status,easing=easing,
                       parameters={"continuity_required":bool(continuity_required),
                                   "constant_rate_semantics":bool(constant_rate_semantics),
                                   "abrupt_state_change":bool(abrupt_state_change)},
                       warnings=warnings,blockers=blockers)
