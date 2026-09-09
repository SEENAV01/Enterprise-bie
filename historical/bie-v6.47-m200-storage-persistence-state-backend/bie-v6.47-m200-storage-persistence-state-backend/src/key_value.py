def record(namespace, key, value, version=1,
           metadata=None):
    if not namespace or not key:
        raise ValueError("INVALID_RECORD_KEY")
    return {"namespace":namespace,"key":key,"value":value,
            "version":version,"metadata":metadata or {}}

def same_key(a,b):
    return a["namespace"]==b["namespace"] and a["key"]==b["key"]
