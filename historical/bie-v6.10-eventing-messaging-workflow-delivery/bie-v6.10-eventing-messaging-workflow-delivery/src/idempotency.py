def idempotency_key(operation,
                   entity_id,request_id):
    return {"operation":operation,
            "entity_id":entity_id,
            "request_id":request_id}

def already_processed(store,key):
    return key in store

def mark_processed(store,key):
    store.add(key)
    return store
