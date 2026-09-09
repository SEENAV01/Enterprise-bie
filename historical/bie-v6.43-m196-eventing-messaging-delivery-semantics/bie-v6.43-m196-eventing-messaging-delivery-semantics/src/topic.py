def topic(topic_id, name, partitions=1,
         retention=None):
    if partitions < 1:
        raise ValueError("INVALID_PARTITIONS")
    return {"topic_id":topic_id,"name":name,
            "partitions":partitions,"retention":retention,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
