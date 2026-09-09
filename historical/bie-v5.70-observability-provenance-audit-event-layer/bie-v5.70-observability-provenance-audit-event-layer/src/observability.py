def metric(name,value,timestamp,labels=None):
    return {"name":name,"value":value,
            "timestamp":timestamp,"labels":labels or {}}

def observation(event_type,entity_ref,status,
                duration_ms=None,error=None,metadata=None):
    return {"event_type":event_type,"entity_ref":entity_ref,
            "status":status,"duration_ms":duration_ms,
            "error":error,"metadata":metadata or {}}
