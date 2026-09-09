def repair_action(failed_checks,evaluation):
    if not failed_checks:
        return {"action":"NONE"}
    return {"action":"REPAIR_AND_REEVALUATE",
            "failed_checks":[c["name"] for c in failed_checks],
            "previous_score":evaluation.get("score")}

def retry_allowed(attempt,max_attempts):
    return attempt < max_attempts
