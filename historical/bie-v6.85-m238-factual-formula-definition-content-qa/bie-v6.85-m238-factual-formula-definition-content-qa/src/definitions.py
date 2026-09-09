def definition(term,statement,required_features=None):
    return {"term":term,"statement":statement,
            "required_features":required_features or []}

def verify_definition(d):
    errors=[]
    if not d.get("term"): errors.append("MISSING_TERM")
    if not d.get("statement"): errors.append("MISSING_STATEMENT")
    for feature in d.get("required_features",[]):
        if feature.lower() not in d["statement"].lower(): errors.append("MISSING_FEATURE:"+feature)
    return {"passed":not errors,"errors":errors}
