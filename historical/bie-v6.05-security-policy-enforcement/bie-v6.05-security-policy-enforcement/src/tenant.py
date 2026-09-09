def tenant_boundary(subject_tenant,
                   resource_tenant):
    return {"subject_tenant":subject_tenant,
            "resource_tenant":resource_tenant,
            "same_tenant":subject_tenant==resource_tenant}

def isolated(subject_tenant,resource_tenant):
    return subject_tenant==resource_tenant
