def feature_flag(flag_id,enabled=False,
                rollout=0,version=1,
                kill_switch=False):
    return {"flag_id":flag_id,"enabled":enabled,
            "rollout":max(0,min(100,rollout)),
            "version":version,
            "kill_switch":kill_switch}

def active(flag):
    return flag.get("enabled",False) and not flag.get("kill_switch",False)
