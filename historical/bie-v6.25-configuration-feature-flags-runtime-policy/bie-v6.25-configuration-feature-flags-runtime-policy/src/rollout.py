def rollout(flag_key,strategy="PERCENTAGE",
            percentage=0,
            segments=None):
    if strategy not in {"ALL","NONE","PERCENTAGE","SEGMENT"}:
        raise ValueError("INVALID_ROLLOUT_STRATEGY")
    if not 0 <= percentage <= 100:
        raise ValueError("INVALID_PERCENTAGE")
    return {"flag_key":flag_key,
            "strategy":strategy,
            "percentage":percentage,
            "segments":segments or []}

def applies(record,percentage=0,segment=None):
    if record["strategy"]=="ALL": return True
    if record["strategy"]=="NONE": return False
    if record["strategy"]=="PERCENTAGE":
        return percentage < record["percentage"]
    return segment in record["segments"]
