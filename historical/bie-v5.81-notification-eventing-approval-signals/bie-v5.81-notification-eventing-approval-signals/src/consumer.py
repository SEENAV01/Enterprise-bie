def delivery_key(event_id,consumer_id):
    return f"{consumer_id}:{event_id}"

def deliver(evt,consumer_id,handler,processed):
    key=delivery_key(evt["event_id"],consumer_id)
    if key in processed:
        return {"status":"DUPLICATE","key":key}
    handler(evt)
    processed.add(key)
    return {"status":"DELIVERED","key":key}
