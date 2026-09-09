def service_identity(service_id,
                    issuer,tenant_id=None,
                    audiences=None):
    return {"service_id":service_id,
            "issuer":issuer,
            "tenant_id":tenant_id,
            "audiences":audiences or [],
            "status":"ACTIVE"}

def revoke(record):
    out=dict(record); out["status"]="REVOKED"; return out
