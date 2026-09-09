def incident(incident_id,title,severity,
             service,started_at,source=None):
    return {"incident_id":incident_id,
            "title":title,"severity":severity,
            "service":service,"started_at":started_at,
            "source":source,"status":"OPEN"}

def resolve(record,resolved_at):
    out=dict(record); out["status"]="RESOLVED"
    out["resolved_at"]=resolved_at
    return out
