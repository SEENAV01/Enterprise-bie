def reload_policy(mode="ON_CHANGE",
                  restart_required=False):
    if mode not in {"ON_CHANGE","PERIODIC","MANUAL"}:
        raise ValueError("INVALID_RELOAD_MODE")
    return {"mode":mode,
            "restart_required":restart_required}

def hot_reload(record):
    return record["mode"] in {"ON_CHANGE","PERIODIC"} and not record["restart_required"]
