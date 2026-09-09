def reconciliation(resource_id,
                    source_state,
                    target_state,
                    started_at):
    return {"resource_id":resource_id,
            "source_state":source_state,
            "target_state":target_state,
            "started_at":started_at,
            "status":"PENDING"}

def mark(record,status):
    if status not in {"PENDING","RUNNING","CONVERGED","FAILED"}:
        raise ValueError("INVALID_RECONCILIATION_STATUS")
    out=dict(record); out["status"]=status; return out
