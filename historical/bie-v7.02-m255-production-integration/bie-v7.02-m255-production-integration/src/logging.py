def log_event(run_id,event_type,message,metadata=None):
    return {"run_id":run_id,"event_type":event_type,"message":message,
            "metadata":metadata or {}}

def summarize_logs(events):
    return {"event_count":len(events),
            "errors":[e for e in events if "ERROR" in e.get("event_type","")],
            "warnings":[e for e in events if "WARN" in e.get("event_type","")]}
