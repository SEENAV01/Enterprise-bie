def reindex(job_id,index,
            from_version,to_version):
    return {"job_id":job_id,
            "index":index,
            "from_version":from_version,
            "to_version":to_version,
            "status":"PLANNED",
            "progress":0}

def advance(record,progress):
    out=dict(record)
    out["progress"]=progress
    out["status"]="COMPLETE" if progress>=100 else "RUNNING"
    return out
