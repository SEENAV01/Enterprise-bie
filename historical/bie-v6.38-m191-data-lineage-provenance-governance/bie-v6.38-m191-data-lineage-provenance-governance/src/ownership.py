def ownership(resource_id, owner, steward=None,
              domain=None):
    return {"resource_id":resource_id,"owner":owner,
            "steward":steward,"domain":domain}

def assigned(record):
    return bool(record["owner"])
