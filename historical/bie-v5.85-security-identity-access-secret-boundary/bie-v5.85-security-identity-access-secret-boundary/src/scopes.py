def resource(resource_id,resource_type,scope,
             owner_id=None):
    return {"resource_id":resource_id,
            "type":resource_type,"scope":scope,
            "owner_id":owner_id}

def in_scope(resource_record,allowed_scopes):
    return resource_record.get("scope") in set(allowed_scopes)
