def span(span_id,trace_id,name,start=None,end=None,
         parent_id=None,attributes=None,status="OK"):
    return {"span_id":span_id,"trace_id":trace_id,"name":name,
            "start":start,"end":end,"parent_id":parent_id,
            "attributes":attributes or {},"status":status}

def trace(trace_id,spans=None):
    return {"trace_id":trace_id,"spans":spans or []}
