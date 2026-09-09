def network_policy(mode="DENY",allowlist=None,
                   max_requests=None):
    return {"mode":mode,"allowlist":allowlist or [],
            "max_requests":max_requests}

def network_check(policy,host):
    if policy.get("mode")=="DENY": return False
    if policy.get("mode")=="ALLOWLIST":
        return host in policy.get("allowlist",[])
    return True
