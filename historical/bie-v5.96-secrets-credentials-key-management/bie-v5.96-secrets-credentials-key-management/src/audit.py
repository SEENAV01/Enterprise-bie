def audit_event(event_id,subject,action,
                service,timestamp,result,
                secret_id=None):
    return {"event_id":event_id,"subject":subject,
            "action":action,"service":service,
            "timestamp":timestamp,"result":result,
            "secret_id":secret_id}

def safe_event(event):
    out=dict(event)
    out.pop("secret_value",None)
    return out
