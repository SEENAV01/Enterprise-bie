def state_owner(key,owner,
               epoch=1):
    if epoch < 1:
        raise ValueError("INVALID_EPOCH")
    return {"key":key,"owner":owner,
            "epoch":epoch,"status":"OWNED"}

def current(record):
    return record["status"]=="OWNED"
