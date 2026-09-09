def pipeline(asset_id,steps=None,
            outputs=None,status="PLANNED"):
    return {"asset_id":asset_id,"steps":steps or [],
            "outputs":outputs or [],"status":status}

def add_step(pipeline_record,step):
    out=dict(pipeline_record)
    out["steps"]=list(pipeline_record.get("steps",[]))+[step]
    return out

def complete(pipeline_record,outputs):
    out=dict(pipeline_record); out["outputs"]=outputs
    out["status"]="COMPLETE"; return out
