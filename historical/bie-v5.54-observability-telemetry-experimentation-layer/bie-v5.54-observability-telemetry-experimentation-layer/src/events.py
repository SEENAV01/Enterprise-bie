def event(event_id,event_type,timestamp=None,entity_refs=None,
          payload=None,context=None):
    return {"event_id":event_id,"event_type":event_type,
            "timestamp":timestamp,"entity_refs":entity_refs or [],
            "payload":payload or {},"context":context or {}}

def event_types():
    return ["LEARNER","CONTENT","PLANNING","GENERATION","RENDER",
            "VALIDATION","CORRECTION","BUILD","SYSTEM","EXPERIMENT"]
