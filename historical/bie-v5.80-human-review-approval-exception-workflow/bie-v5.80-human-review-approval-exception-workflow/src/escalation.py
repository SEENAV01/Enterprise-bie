def escalation(review_id,reason,target_role):
    return {"review_id":review_id,"reason":reason,
            "target_role":target_role,"state":"ESCALATED"}

def needs_escalation(severity):
    return severity in {"CRITICAL","BLOCKING"}
