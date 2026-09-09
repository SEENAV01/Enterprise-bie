def provenance_event(event,actor,timestamp,
                     details=None):
    return {"event":event,"actor":actor,
            "timestamp":timestamp,"details":details or {}}

def append(history,event):
    return history+[event]
