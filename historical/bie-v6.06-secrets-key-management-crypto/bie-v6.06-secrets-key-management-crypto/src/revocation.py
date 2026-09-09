def revocation(material_id,version,
                  revoked_at,reason):
    return {"material_id":material_id,
            "version":version,
            "revoked_at":revoked_at,
            "reason":reason,
            "status":"REVOKED"}

def revoked(record):
    return record.get("status")=="REVOKED"
