def ownership_epoch(resource_id,
                    epoch,
                    owner):
    if epoch < 1:
        raise ValueError("INVALID_EPOCH")
    return {"resource_id":resource_id,
            "epoch":epoch,
            "owner":owner}

def newer(candidate,current):
    return candidate["epoch"] > current["epoch"]
