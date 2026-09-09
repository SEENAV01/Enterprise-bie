def span(span_id,trace_id,parent_span_id,
         operation,service,start,end=None,
         status="OK",attributes=None):
    return {"span_id":span_id,"trace_id":trace_id,
            "parent_span_id":parent_span_id,
            "operation":operation,"service":service,
            "start":start,"end":end,"status":status,
            "attributes":attributes or {}}

def duration(s):
    if s.get("end") is None: return None
    return s["end"]-s["start"]
