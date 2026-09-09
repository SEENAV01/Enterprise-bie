def event(event_id,event_type,payload,
          producer,correlation_id=None,causation_id=None,
          schema_version="1"):
    return {"event_id":event_id,"event_type":event_type,
            "payload":payload,"producer":producer,
            "correlation_id":correlation_id,
            "causation_id":causation_id,
            "schema_version":schema_version}

def command(command_id,command_type,payload,
            producer,correlation_id=None,causation_id=None):
    return {"command_id":command_id,
            "command_type":command_type,"payload":payload,
            "producer":producer,
            "correlation_id":correlation_id,
            "causation_id":causation_id}
