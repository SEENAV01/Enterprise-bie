def quality_checks(component):
    errors=[]; warnings=[]
    if not component.get("type"): errors.append("MISSING_TYPE")
    if component.get("type")=="GRAPH":
        if not component.get("x") or not component.get("series"):
            errors.append("INCOMPLETE_GRAPH")
    if component.get("type")=="DIAGRAM" and not component.get("edges"):
        warnings.append("DIAGRAM_WITHOUT_EDGES")
    if component.get("type")=="TEXT" and len(component.get("text",""))>180:
        warnings.append("TEXT_OVERLOAD")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
