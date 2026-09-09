def stampede_policy(cache,
                   strategy="SINGLE_FLIGHT",
                   max_waiters=100):
    if strategy not in {"SINGLE_FLIGHT",
                        "REQUEST_COALESCING",
                        "JITTERED_TTL"}:
        raise ValueError("INVALID_STAMPEDE_STRATEGY")
    return {"cache":cache,
            "strategy":strategy,
            "max_waiters":max_waiters}

def protected(record):
    return record["strategy"] in {
        "SINGLE_FLIGHT","REQUEST_COALESCING","JITTERED_TTL"}
