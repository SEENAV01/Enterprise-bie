from contracts import REQUIRED_STAGES

def validate_pipeline(run):
    errors=[]
    if not run.get("run_id"): errors.append("MISSING_RUN_ID")
    if not run.get("source_ref"): errors.append("MISSING_SOURCE")
    stages=[x.get("stage") for x in run.get("stages",[])]
    if stages!=REQUIRED_STAGES: errors.append("INVALID_STAGE_ORDER")
    return {"valid":not errors,"errors":errors}

def complete(run):
    return all(x["status"]=="COMPLETE" for x in run["stages"])
