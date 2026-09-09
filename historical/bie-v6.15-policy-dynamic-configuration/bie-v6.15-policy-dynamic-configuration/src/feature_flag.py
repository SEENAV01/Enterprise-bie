def feature_flag(name,
                enabled=False,
                rollout=0,
                scope=None):
    return {"name":name,
            "enabled":enabled,
            "rollout":rollout,
            "scope":scope}

def active(record,percentage=0):
    return record["enabled"] and percentage < record["rollout"]
