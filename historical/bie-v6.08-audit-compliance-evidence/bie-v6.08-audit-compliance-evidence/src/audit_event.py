def audit_event(event_id,event_type,
                actor,resource,action,
                outcome,timestamp,
                trace_id=None,policy_version=None,
                evidence_refs=None):
    return {"event_id":event_id,
            "event_type":event_type,
            "actor":actor,"resource":resource,
            "action":action,"outcome":outcome,
            "timestamp":timestamp,
            "trace_id":trace_id,
            "policy_version":policy_version,
            "evidence_refs":evidence_refs or []}
