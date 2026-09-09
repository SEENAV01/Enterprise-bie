def snapshot(snapshot_id, namespace,
             version, created_at=None):
    return {"snapshot_id":snapshot_id,"namespace":namespace,
            "version":version,"created_at":created_at,
            "status":"AVAILABLE"}

def available(record):
    return record["status"]=="AVAILABLE"
