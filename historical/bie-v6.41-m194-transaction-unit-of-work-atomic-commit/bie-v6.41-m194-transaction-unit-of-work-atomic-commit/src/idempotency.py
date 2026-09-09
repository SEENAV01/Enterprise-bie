def idempotency(key, operation_hash,
                result_ref=None):
    return {"key":key,"operation_hash":operation_hash,
            "result_ref":result_ref,"status":"ACTIVE"}

def matches(record,key,operation_hash):
    return record["key"]==key and record["operation_hash"]==operation_hash
