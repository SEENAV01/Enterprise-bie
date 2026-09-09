from contracts import REQUIRED_STAGES, stage_contract

def pipeline_run(run_id, source_ref, options=None):
    stages=[stage_contract(s) for s in REQUIRED_STAGES]
    return {"run_id":run_id,"source_ref":source_ref,
            "options":options or {},"stages":stages,
            "status":"CREATED"}

def advance(run, stage, status="COMPLETE",
            output_ref=None, errors=None):
    out=dict(run)
    out["stages"]=[dict(x) for x in run["stages"]]
    for x in out["stages"]:
        if x["stage"]==stage:
            x["status"]=status
            x["output_ref"]=output_ref
            x["errors"]=errors or []
            break
    return out
