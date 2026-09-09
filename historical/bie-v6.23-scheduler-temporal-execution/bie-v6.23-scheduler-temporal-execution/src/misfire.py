def misfire_policy(strategy="SKIP",
                  grace_period=0):
    if strategy not in {"SKIP","RUN_NOW",
                        "CATCH_UP","COALESCE"}:
        raise ValueError("INVALID_MISFIRE_STRATEGY")
    return {"strategy":strategy,
            "grace_period":grace_period}

def action(record,missed):
    if not missed:
        return "NORMAL"
    return record["strategy"]
