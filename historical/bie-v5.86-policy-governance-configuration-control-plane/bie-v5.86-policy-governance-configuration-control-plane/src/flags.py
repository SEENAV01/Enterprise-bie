def feature_flag(name,enabled=False,
                environments=None,rollout=1.0):
    return {"name":name,"enabled":enabled,
            "environments":environments or [],
            "rollout":rollout}

def enabled(flag,environment):
    return bool(flag.get("enabled")) and (
        not flag.get("environments") or
        environment in flag["environments"])
