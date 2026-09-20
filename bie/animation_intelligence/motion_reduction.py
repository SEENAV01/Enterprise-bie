from .easing_contracts import *

HIGH_MOTION={"camera","path_follow","trace","morph","simulation_state"}

def apply_motion_reduction(ctx, *, current_easing, current_duration_ms,
                           action_payload=None, essential_semantic_motion=False):
    current_easing=tok(current_easing,"current_easing")
    if isinstance(current_duration_ms,bool) or not isinstance(current_duration_ms,int) or current_duration_ms<1:
        raise DurationError("current_duration_ms invalid")
    payload=dict(action_payload or {})
    if not ctx.reduced_motion_requested:
        return make_policy(ctx,suffix=":motion-reduction",status="PASS",easing=current_easing,
                           duration_ms=current_duration_ms,
                           parameters={"reduced_motion_applied":False,"action_payload":payload})
    warnings=[]
    action=ctx.semantic_action
    easing=current_easing
    duration=current_duration_ms
    replacement=action
    if action=="camera":
        replacement="static_focus"
        easing="step"
        duration=min(duration,250)
    elif action=="path_follow":
        replacement="path_endpoints_with_progress_marker" if essential_semantic_motion else "static_path"
        easing="linear"
        duration=min(duration,400)
    elif action=="trace":
        replacement="progressive_static_trace" if essential_semantic_motion else "static_trace"
        easing="linear"
        duration=min(duration,450)
    elif action=="morph":
        replacement="crossfade_states"
        easing="ease_in_out"
        duration=min(duration,350)
    elif action=="simulation_state":
        replacement="state_snapshots"
        easing="step"
        duration=min(duration,450)
    else:
        duration=min(duration,500)
    if essential_semantic_motion:
        warnings.append("essential_motion_preserved_in_reduced_form")
    return make_policy(ctx,suffix=":motion-reduction",status="REVIEW" if warnings else "PASS",
                       easing=easing,duration_ms=max(1,duration),
                       parameters={"reduced_motion_applied":True,"replacement_action":replacement,
                                   "essential_semantic_motion":bool(essential_semantic_motion),
                                   "action_payload":payload},
                       warnings=warnings)
