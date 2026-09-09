def validate_render_spec(result):
    errors=[]; warnings=[]
    spec=result["renderer_spec"]
    if spec["duration_frames"]<=0: errors.append("INVALID_DURATION")
    if spec["fps"]<=0: errors.append("INVALID_FPS")
    if result["composition"]["durationInFrames"]!=spec["duration_frames"]:
        errors.append("DURATION_MISMATCH")
    if not spec.get("scenes"): warnings.append("NO_SCENES")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
