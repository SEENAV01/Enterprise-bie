def lease(lease_id, artifact_id, owner, expires_at):
    return {"lease_id":lease_id,"artifact_id":artifact_id,
            "owner":owner,"expires_at":expires_at}

def valid(l):
    return bool(l["lease_id"] and l["artifact_id"] and l["owner"])
