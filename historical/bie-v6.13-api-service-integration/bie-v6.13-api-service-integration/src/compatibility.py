POLICIES={"BACKWARD","FORWARD","FULL","NONE"}

def compatibility_policy(scope,mode):
    if mode not in POLICIES:
        raise ValueError("INVALID_COMPATIBILITY_POLICY")
    return {"scope":scope,"mode":mode}

def allows(policy,direction):
    mode=policy["mode"]
    return mode=="FULL" or mode==direction or mode=="NONE" and False
