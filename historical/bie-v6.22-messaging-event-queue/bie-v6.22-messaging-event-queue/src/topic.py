def topic(name, retention=None,
          partitions=1, ordered=False):
    if partitions < 1:
        raise ValueError("INVALID_PARTITIONS")
    return {"name":name,
            "retention":retention,
            "partitions":partitions,
            "ordered":ordered}

def supports_order(record):
    return record["ordered"]
