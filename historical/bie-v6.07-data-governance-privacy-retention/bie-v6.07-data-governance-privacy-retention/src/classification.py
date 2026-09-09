LEVELS={"PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"}

def classification(label,owner=None,reason=None):
    if label not in LEVELS:
        raise ValueError("INVALID_CLASSIFICATION")
    return {"label":label,"owner":owner,"reason":reason}

def at_least(record,minimum):
    order=["PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"]
    return order.index(record["label"])>=order.index(minimum)
