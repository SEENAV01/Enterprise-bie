def audit_event(event_id,job_id,event_type,actor,
               decision=None,resource=None,details=None,timestamp=None):
    return {"event_id":event_id,"job_id":job_id,
            "event_type":event_type,"actor":actor,
            "decision":decision,"resource":resource,
            "details":details or {},"timestamp":timestamp}
