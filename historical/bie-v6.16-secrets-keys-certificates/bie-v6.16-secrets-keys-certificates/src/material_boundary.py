def material_boundary(resource_id,
                      material_type,
                      storage_provider,
                      exportable=False):
    return {"resource_id":resource_id,
            "material_type":material_type,
            "storage_provider":storage_provider,
            "exportable":exportable,
            "material_present":False}

def protected(record):
    return not record["material_present"] and not record["exportable"]
