def validate(result):
    errors=[]; warnings=[]
    if result["collisions"]:
        errors.append("LAYOUT_COLLISION")
    if result["cognitive_load"]["level"]=="HIGH":
        warnings.append("HIGH_COGNITIVE_LOAD")
    if not result["objects"]:
        warnings.append("EMPTY_SCENE")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
