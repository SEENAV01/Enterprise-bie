LEVELS={"PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"}

def classification(data_id,level,
                   categories=None,tenant_id=None):
    if level not in LEVELS:
        raise ValueError("INVALID_DATA_CLASSIFICATION")
    return {"data_id":data_id,"level":level,
            "categories":categories or [],
            "tenant_id":tenant_id}

def is_restricted(record):
    return record["level"] in {"CONFIDENTIAL","RESTRICTED"}
