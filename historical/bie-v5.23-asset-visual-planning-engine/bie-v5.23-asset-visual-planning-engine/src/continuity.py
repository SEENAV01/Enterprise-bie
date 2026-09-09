def continuity_requirements(style_token=None,
                           identity_refs=None,coordinate_system=None):
    return {"style_token":style_token,"identity_refs":identity_refs or [],
            "coordinate_system":coordinate_system}

def check_continuity(specs):
    errors=[]
    tokens={s.get("style_token") for s in specs if s.get("style_token")}
    if len(tokens)>1: errors.append("STYLE_TOKEN_DRIFT")
    return {"valid":not errors,"errors":errors}
