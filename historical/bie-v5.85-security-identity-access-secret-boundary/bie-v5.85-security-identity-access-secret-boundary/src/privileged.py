def privileged_action(action,required_role,
                    justification_required=True):
    return {"action":action,"required_role":required_role,
            "justification_required":justification_required}

def validate_privileged_request(request,record):
    if request.get("action")!=record.get("action"):
        return False
    if record.get("justification_required") and not request.get("justification"):
        return False
    return record.get("required_role") in set(request.get("roles",[]))
