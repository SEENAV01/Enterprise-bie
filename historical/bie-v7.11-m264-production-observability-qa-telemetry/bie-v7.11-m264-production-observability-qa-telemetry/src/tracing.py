def start_span(trace_id, span_id, name, parent_id=None):
    return {"trace_id":trace_id,"span_id":span_id,"parent_id":parent_id,
            "name":name,"status":"RUNNING"}

def finish_span(span, status="OK", attributes=None):
    span["status"]=status
    span["attributes"]=attributes or {}
    return span
