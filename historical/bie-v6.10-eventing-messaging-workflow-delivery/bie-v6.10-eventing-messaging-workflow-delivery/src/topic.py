def topic(name,partitions=1,
          retention_seconds=None):
    return {"name":name,
            "partitions":partitions,
            "retention_seconds":retention_seconds}

def valid(topic_record):
    return topic_record["partitions"]>0
