def quality_hook(dataset_id, check_id,
                 metric, threshold=None):
    return {"dataset_id":dataset_id,"check_id":check_id,
            "metric":metric,"threshold":threshold}

def passed(record,value):
    return record["threshold"] is None or value >= record["threshold"]
