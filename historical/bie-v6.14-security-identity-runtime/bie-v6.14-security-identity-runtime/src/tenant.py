def tenant_boundary(tenant_id,
                    resource_tenant_id):
    return {"tenant_id":tenant_id,
            "resource_tenant_id":resource_tenant_id,
            "status":"MATCHED"
            if tenant_id==resource_tenant_id
            else "VIOLATION"}

def isolated(record):
    return record["status"]=="MATCHED"
