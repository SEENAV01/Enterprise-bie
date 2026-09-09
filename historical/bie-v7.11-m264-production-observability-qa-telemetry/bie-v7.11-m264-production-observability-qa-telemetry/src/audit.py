def audit_record(run_id, actor, action, target, result, reason=None):
    return {"run_id":run_id,"actor":actor,"action":action,"target":target,
            "result":result,"reason":reason}

def verify_audit(records):
    required={"run_id","actor","action","target","result"}
    return {"valid":all(required.issubset(r) for r in records),
            "count":len(records)}
