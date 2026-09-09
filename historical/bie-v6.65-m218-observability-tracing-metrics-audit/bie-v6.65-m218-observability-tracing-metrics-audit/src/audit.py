def audit_event(event_id,actor,action,target,result,
                trace_id=None,metadata=None):
    return {"event_id":event_id,"actor":actor,"action":action,
            "target":target,"result":result,"trace_id":trace_id,
            "metadata":metadata or {}}
def valid(e): return all(e.get(k) for k in
    ("event_id","actor","action","target","result"))
