def savepoint(tx_id, name, sequence):
    return {"tx_id":tx_id,"name":name,
            "sequence":sequence,"status":"ACTIVE"}

def valid(record):
    return bool(record["name"]) and record["sequence"]>=0
