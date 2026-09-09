def cancellation(task_id, reason=None,
                  requested_by=None):
    return {"task_id":task_id,"reason":reason,
            "requested_by":requested_by,"status":"REQUESTED"}

def requested(record):
    return record["status"]=="REQUESTED"
