import uuid, time

def trace(trace_id=None):
    return {"trace_id":trace_id or str(uuid.uuid4()),
            "spans":[]}

def span(name,trace_id,parent_id=None):
    return {"span_id":str(uuid.uuid4()),
            "trace_id":trace_id,"parent_id":parent_id,
            "name":name,"start":time.time(),
            "end":None,"attributes":{}}

def finish(s):
    out=dict(s); out["end"]=time.time(); return out
