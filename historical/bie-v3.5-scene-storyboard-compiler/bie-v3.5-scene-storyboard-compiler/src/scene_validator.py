def validate_scene(scene):
    errors=[]
    if not scene.get("narration_unit_ids"): errors.append("NO_NARRATION")
    if not scene.get("visual_elements"): errors.append("NO_VISUAL_STAGING")
    if not scene.get("animation_events"): errors.append("NO_ANIMATION_PLAN")
    if scene.get("duration_policy")!="AUDIO_DRIVEN": errors.append("INVALID_TIMING_POLICY")
    return {"valid":not errors,"errors":errors}
