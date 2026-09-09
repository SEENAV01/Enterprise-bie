def privacy_boundary(resource,
                    tenant_id,
                    allowed_purposes,
                    minimum_access=True):
    return {"resource":resource,
            "tenant_id":tenant_id,
            "allowed_purposes":allowed_purposes,
            "minimum_access":minimum_access}

def purpose_allowed(record,purpose):
    return purpose in record["allowed_purposes"]
