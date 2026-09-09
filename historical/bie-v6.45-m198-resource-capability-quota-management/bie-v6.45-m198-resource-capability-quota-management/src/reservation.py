def reservation(reservation_id, subject,
                 resource, amount, start_at=None,
                 end_at=None):
    if amount <= 0:
        raise ValueError("INVALID_RESERVATION_AMOUNT")
    return {"reservation_id":reservation_id,"subject":subject,
            "resource":resource,"amount":amount,
            "start_at":start_at,"end_at":end_at,
            "status":"PENDING"}

def active(record):
    return record["status"]=="ACTIVE"

def activate(record):
    out=dict(record); out["status"]="ACTIVE"; return out
