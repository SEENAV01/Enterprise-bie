def log_event(timestamp,level,message,
              service,trace_id=None,span_id=None,
              correlation_id=None,fields=None):
    return {"timestamp":timestamp,"level":level,
            "message":message,"service":service,
            "trace_id":trace_id,"span_id":span_id,
            "correlation_id":correlation_id,
            "fields":fields or {}}

def safe_log(event):
    out=dict(event)
    fields=dict(out.get("fields") or {})
    fields.pop("secret",None)
    fields.pop("token",None)
    out["fields"]=fields
    return out
