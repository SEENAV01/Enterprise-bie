def resource_policy(service,
                    quotas=None,
                    rate_limits=None,
                    concurrency=None,
                    budgets=None):
    return {"service":service,
            "quotas":quotas or [],
            "rate_limits":rate_limits or [],
            "concurrency":concurrency or [],
            "budgets":budgets or []}

def governance_ready(policy):
    return policy.get("service") is not None
