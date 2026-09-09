def validate_accessibility(scene):
    errors=[]
    if scene.get("text_contrast_ratio",0)<4.5: errors.append("CONTRAST_BELOW_AA")
    if not scene.get("narration_present",False): errors.append("NARRATION_MISSING")
    if not scene.get("captions_present",False): errors.append("CAPTIONS_MISSING")
    return {"valid":not errors,"errors":errors}
