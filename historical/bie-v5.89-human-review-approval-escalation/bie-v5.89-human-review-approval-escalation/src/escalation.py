def escalation(item_id,reason,target_role,
               urgency="HIGH"):
    return {"item_id":item_id,"reason":reason,
            "target_role":target_role,"urgency":urgency,
            "status":"OPEN"}

def resolve(record,resolver,decision):
    out=dict(record); out["resolver"]=resolver
    out["resolution"]=decision; out["status"]="RESOLVED"
    return out
