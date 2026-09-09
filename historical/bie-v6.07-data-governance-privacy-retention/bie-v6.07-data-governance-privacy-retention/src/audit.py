def governance_audit(event_id,
                    resource_id,action,
                    actor,timestamp,
                    outcome,reason=None):
    return {"event_id":event_id,
            "resource_id":resource_id,
            "action":action,"actor":actor,
            "timestamp":timestamp,
            "outcome":outcome,"reason":reason}
