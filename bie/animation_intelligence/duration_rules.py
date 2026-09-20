from .easing_contracts import *

BASE_MS={
    "enter":450,"exit":350,"emphasize":600,"reveal":550,"transform":800,
    "morph":900,"trace":1000,"path_follow":1200,"camera":900,"simulation_state":700
}

def resolve_duration(ctx, *, narration_window_ms, min_ms=None, max_ms=None,
                     semantic_steps=1, allow_scene_extension=True):
    if ctx.semantic_action not in BASE_MS:
        return make_policy(ctx,suffix=":duration",status="UNSUPPORTED",easing="linear",
                           blockers=("unsupported_semantic_action",))
    if isinstance(narration_window_ms,bool) or not isinstance(narration_window_ms,int) or narration_window_ms<1:
        raise DurationError("narration_window_ms invalid")
    if isinstance(semantic_steps,bool) or not isinstance(semantic_steps,int) or semantic_steps<1:
        raise DurationError("semantic_steps invalid")
    lo=120 if min_ms is None else int(min_ms)
    hi=5000 if max_ms is None else int(max_ms)
    if lo<1 or hi<lo:
        raise DurationError("invalid duration bounds")
    base=BASE_MS[ctx.semantic_action]
    complexity_factor=0.75 + 0.75*ctx.complexity
    step_factor=1 + min(semantic_steps-1,6)*0.18
    importance_factor=0.9 + 0.25*ctx.semantic_importance
    desired=round(base*complexity_factor*step_factor*importance_factor)
    desired=max(lo,min(hi,desired))
    warnings=[]; blockers=[]
    duration=desired
    if desired>narration_window_ms:
        if allow_scene_extension:
            warnings.append("scene_extension_required_to_preserve_semantic_duration")
            duration=desired
        else:
            blockers.append("narration_window_too_short_for_semantic_duration")
            duration=narration_window_ms
    elif narration_window_ms>desired*4:
        warnings.append("large_idle_gap_after_motion_may_need_hold_or_recomposition")
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return make_policy(ctx,suffix=":duration",status=status,easing="linear",duration_ms=max(1,duration),
                       parameters={"desired_ms":desired,"narration_window_ms":narration_window_ms,
                                   "semantic_steps":semantic_steps,"min_ms":lo,"max_ms":hi,
                                   "allow_scene_extension":bool(allow_scene_extension)},
                       warnings=warnings,blockers=blockers)
