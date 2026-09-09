def notification(event_id,channel,recipient,
                template,payload=None):
    return {"event_id":event_id,"channel":channel,
            "recipient":recipient,"template":template,
            "payload":payload or {},"status":"PENDING"}

def mark_sent(record):
    out=dict(record); out["status"]="SENT"; return out

def mark_failed(record,error):
    out=dict(record); out["status"]="FAILED"; out["error"]=error
    return out
