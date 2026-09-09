import uuid, time

def event(event_type,payload,source="bie",correlation_id=None,
          causation_id=None,event_id=None):
    return {"schema_version":"5.81",
            "event_id":event_id or str(uuid.uuid4()),
            "event_type":event_type,"source":source,
            "timestamp":time.time(),
            "correlation_id":correlation_id,
            "causation_id":causation_id,
            "payload":payload}
