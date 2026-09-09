def make_event(event_id,event_type,aggregate_id,sequence,payload=None):
    return {"event_id":event_id,"event_type":event_type,"aggregate_id":aggregate_id,
            "sequence":sequence,"payload":payload or {}}

def event_key(e):
    return f"{e['aggregate_id']}:{e['sequence']}"
