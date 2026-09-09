def secret_audit(event_id,
                resource_id,action,
                actor,result,reason=None):
    return {"event_id":event_id,
            "resource_id":resource_id,
            "action":action,
            "actor":actor,
            "result":result,
            "reason":reason}
