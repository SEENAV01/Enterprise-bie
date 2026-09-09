def audit_event(event_id,actor,action,key,
                old_version,new_version,timestamp,
                reason=None):
    return {"event_id":event_id,"actor":actor,
            "action":action,"key":key,
            "old_version":old_version,
            "new_version":new_version,
            "timestamp":timestamp,"reason":reason}
