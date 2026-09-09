def event(event_id,event_type,
          payload_ref,producer,
          timestamp,tenant_id=None,
          schema_version=None):
    return {"event_id":event_id,
            "event_type":event_type,
            "payload_ref":payload_ref,
            "producer":producer,
            "timestamp":timestamp,
            "tenant_id":tenant_id,
            "schema_version":schema_version}

def event_key(record):
    return (record.get("tenant_id"),
            record["event_type"],record["event_id"])
