def tenant_data(resource_id,tenant_id):
    return {"resource_id":resource_id,
            "tenant_id":tenant_id}

def same_tenant(resource,tenant_id):
    return resource.get("tenant_id")==tenant_id
