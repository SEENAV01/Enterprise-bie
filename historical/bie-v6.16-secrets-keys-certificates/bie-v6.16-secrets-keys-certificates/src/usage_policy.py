def key_usage_policy(key_id,
                    allowed_usages,
                    allowed_services=None,
                    tenant_bound=True):
    return {"key_id":key_id,
            "allowed_usages":allowed_usages,
            "allowed_services":allowed_services or [],
            "tenant_bound":tenant_bound}

def allows(policy,usage,service=None):
    usage_ok=usage in policy["allowed_usages"]
    service_ok=(not policy["allowed_services"] or
                service in policy["allowed_services"])
    return usage_ok and service_ok
