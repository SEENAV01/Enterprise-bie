def degradation_policy(service,
                       fallback=None,
                       max_error_rate=None):
    return {"service":service,
            "fallback":fallback,
            "max_error_rate":max_error_rate}

def fallback_target(policy):
    return policy.get("fallback")
