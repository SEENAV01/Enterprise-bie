def consumer_key(consumer_id,event_id):
    return f"{consumer_id}:{event_id}"

def consume_once(seen,event_id,consumer_id):
    key=consumer_key(consumer_id,event_id)
    if key in seen:
        return False
    seen.add(key)
    return True
