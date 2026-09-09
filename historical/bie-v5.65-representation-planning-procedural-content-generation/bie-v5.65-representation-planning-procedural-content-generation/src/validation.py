def validation_contract(checks=None,
                        tolerance=None,visual=None,
                        semantic=None,structural=None):
    return {"checks":checks or [],
            "tolerance":tolerance,
            "visual":visual or {},
            "semantic":semantic or {},
            "structural":structural or {}}

def validate_representation(artifact,contract):
    errors=[]
    for check in contract.get("checks",[]):
        if check=="HAS_OUTPUT" and not artifact.get("output_ref"):
            errors.append(check)
        if check=="HAS_SEMANTIC_REFS" and not artifact.get("semantic_refs"):
            errors.append(check)
    return {"valid":not errors,"errors":errors}
