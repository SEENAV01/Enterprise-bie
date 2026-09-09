def transaction_event(event_id, tx_id,
                      operation, status, actor=None):
    return {"event_id":event_id,"tx_id":tx_id,
            "operation":operation,"status":status,"actor":actor}

def successful(record):
    return record["status"]=="SUCCESS"
