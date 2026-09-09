def suppression(rule_id,reason,
                starts_at,ends_at=None):
    return {"rule_id":rule_id,"reason":reason,
            "starts_at":starts_at,"ends_at":ends_at,
            "status":"ACTIVE"}

def active(record,now):
    end=record.get("ends_at")
    return record.get("status")=="ACTIVE" and (
        end is None or now < end)
