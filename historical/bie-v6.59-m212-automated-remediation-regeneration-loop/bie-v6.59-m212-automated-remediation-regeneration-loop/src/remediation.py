SUPPORTED_ACTIONS = {
    "REGENERATE_ASSET","REGENERATE_AUDIO","REBUILD_SCENE",
    "REPAIR_TIMING","REPAIR_CAPTION","RERENDER","ESCALATE"
}

def remediation(action_id, action, target_refs, reason,
                 preserve_refs=None, parameters=None):
    if action not in SUPPORTED_ACTIONS:
        raise ValueError("UNSUPPORTED_REMEDIATION_ACTION")
    return {"action_id":action_id,"action":action,
            "target_refs":target_refs,"reason":reason,
            "preserve_refs":preserve_refs or [],
            "parameters":parameters or {}}

def valid(a):
    return bool(a["action_id"] and a["target_refs"] and a["reason"])
