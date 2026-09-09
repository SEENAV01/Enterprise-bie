def renderability_check(spec):
    errors=[]
    if spec.get("render_target")!="REMOTION":
        errors.append("UNSUPPORTED_RENDER_TARGET")
    if not spec.get("modality"): errors.append("MISSING_MODALITY")
    for p in spec.get("primitives",[]):
        if not p.get("kind"): errors.append("INVALID_PRIMITIVE")
    return {"valid":not errors,"errors":errors}
