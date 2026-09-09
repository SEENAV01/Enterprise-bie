def event(event_id,event_type,
          payload_ref,
          tenant_id=None,
          correlation_id=None,
          causation_id=None,
          version=1):
    return {"event_id":event_id,
            "event_type":event_type,
            "payload_ref":payload_ref,
            "tenant_id":tenant_id,
            "correlation_id":correlation_id,
            "causation_id":causation_id,
            "version":version}

def same_correlation(a,b):
    return a["correlation_id"]==b["correlation_id"]
