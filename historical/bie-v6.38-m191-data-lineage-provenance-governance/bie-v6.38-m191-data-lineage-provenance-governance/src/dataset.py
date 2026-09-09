def dataset(dataset_id, name, owner=None, classification=None):
    if not dataset_id or not name:
        raise ValueError("INVALID_DATASET")
    return {"dataset_id":dataset_id,"name":name,"owner":owner,
            "classification":classification,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
