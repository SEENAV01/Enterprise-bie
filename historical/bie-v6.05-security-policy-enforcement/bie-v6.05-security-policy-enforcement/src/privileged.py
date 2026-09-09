def privileged_operation(action,
                         resource,requires_step_up=True,
                         requires_audit=True):
    return {"action":action,"resource":resource,
            "requires_step_up":requires_step_up,
            "requires_audit":requires_audit}

def controls_required(operation):
    return [x for x in
            ["STEP_UP_AUTH","AUDIT"]
            if operation.get({
                "STEP_UP_AUTH":"requires_step_up",
                "AUDIT":"requires_audit"}[x])]
