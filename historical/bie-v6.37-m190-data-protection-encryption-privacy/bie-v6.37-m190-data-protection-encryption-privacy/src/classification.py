def classification(data_type, level="INTERNAL", tags=None):
    if level not in {"PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"}:
        raise ValueError("INVALID_CLASSIFICATION")
    return {"data_type":data_type,"level":level,"tags":tags or []}

def is_restricted(record):
    return record["level"] in {"CONFIDENTIAL","RESTRICTED"}
