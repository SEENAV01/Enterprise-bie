def network_policy(mode="DENY",allowlist=None):
    return {"mode":mode,"allowlist":allowlist or []}

def network_allowed(policy,host=None):
    if policy.get("mode")=="DENY": return False
    if policy.get("mode")=="ALLOWLIST":
        return host in set(policy.get("allowlist",[]))
    return False
