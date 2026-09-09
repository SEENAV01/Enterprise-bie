def fencing_token(resource_id,epoch):
    if epoch < 1:
        raise ValueError("INVALID_EPOCH")
    return {"resource_id":resource_id,
            "epoch":epoch}

def permits(record,request_epoch):
    return request_epoch >= record["epoch"]
