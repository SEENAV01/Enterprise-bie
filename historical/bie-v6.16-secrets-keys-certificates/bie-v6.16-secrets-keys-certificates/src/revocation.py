def revocation(item_id,item_type,
              reason,revoked_at):
    return {"item_id":item_id,
            "item_type":item_type,
            "reason":reason,
            "revoked_at":revoked_at,
            "status":"REVOKED"}

def is_revoked(record):
    return record["status"]=="REVOKED"
