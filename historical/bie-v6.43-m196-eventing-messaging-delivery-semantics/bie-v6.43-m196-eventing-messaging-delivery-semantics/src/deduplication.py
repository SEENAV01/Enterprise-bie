def deduplication(key, window_ms=None):
    return {"key":key,"window_ms":window_ms,"status":"ACTIVE"}

def matches(record, key):
    return record["key"]==key and record["status"]=="ACTIVE"
