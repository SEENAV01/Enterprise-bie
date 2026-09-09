def service_identity(service_id, audience,
                    credential_ref=None):
    return {"service_id":service_id,
            "audience":audience,
            "credential_ref":credential_ref,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
