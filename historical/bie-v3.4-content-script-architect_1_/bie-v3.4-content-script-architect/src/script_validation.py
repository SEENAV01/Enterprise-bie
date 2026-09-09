def validate_script(script):
    errors=[]
    for u in script.get("units",[]):
        if u["type"] not in ["HOOK","CONTEXT","TRANSITION"] and not u.get("evidence_ids"):
            errors.append("UNGROUNDED_UNIT:"+u["id"])
        if not u.get("text","").strip():
            errors.append("EMPTY_UNIT:"+u["id"])
    return {"valid":not errors,"errors":errors}
