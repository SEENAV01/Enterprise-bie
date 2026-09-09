def validate_derivation(steps):
    ids={s["step_id"] for s in steps}
    errors=[]
    for s in steps:
        if s.get("from_step") and s["from_step"] not in ids:
            errors.append("MISSING_DERIVATION_PARENT")
    return {"valid":not errors,"errors":errors}

def validate_graph(g):
    errors=[]
    if len(g.get("domain",[]))!=2: errors.append("INVALID_DOMAIN")
    if not g.get("x_label") or not g.get("y_label"):
        errors.append("MISSING_AXIS_LABEL")
    return {"valid":not errors,"errors":errors}

def validate_visual_semantics(v):
    errors=[]
    if not v.get("concept_id"): errors.append("MISSING_CONCEPT_LINK")
    if v.get("mathematical_state") is None:
        errors.append("MISSING_MATH_STATE")
    return {"valid":not errors,"errors":errors}
