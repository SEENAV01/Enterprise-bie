def audit_action(run_id, actor, action, before, after, reason=None):
    return {"run_id":run_id,"actor":actor,"action":action,"before":before,
            "after":after,"reason":reason}

def validate_chain(records):
    errors=[]
    for i,r in enumerate(records):
        if i and records[i-1]["run_id"]!=r["run_id"]: errors.append("AUDIT_RUN_MISMATCH")
        if r["before"]==r["after"] and r["action"] in {"PAUSE","RESUME","CANCEL","RELEASE"}:
            errors.append("AUDIT_NO_STATE_CHANGE")
    return {"valid":not errors,"errors":errors}
