def validate_dsl(spec):
    errors=[]
    if spec.get("dsl_version")!="1.0": errors.append("DSL_VERSION")
    if spec.get("duration",{}).get("mode")!="AUDIO_DRIVEN": errors.append("TIMING_NOT_AUDIO_DRIVEN")
    if not spec.get("scene_id"): errors.append("NO_SCENE_ID")
    return {"valid":not errors,"errors":errors}
