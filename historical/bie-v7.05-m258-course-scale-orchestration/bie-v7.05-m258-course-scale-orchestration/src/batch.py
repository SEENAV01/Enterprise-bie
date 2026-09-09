def create_batch(items, batch_id):
    return {"batch_id":batch_id,"items":items,"status":"QUEUED",
            "completed":0,"failed":0}

def update_batch(batch, item_status):
    if item_status=="SUCCEEDED": batch["completed"]+=1
    elif item_status=="FAILED": batch["failed"]+=1
    total=len(batch["items"])
    if batch["completed"]+batch["failed"]==total:
        batch["status"]="FAILED" if batch["failed"] else "SUCCEEDED"
    return batch
