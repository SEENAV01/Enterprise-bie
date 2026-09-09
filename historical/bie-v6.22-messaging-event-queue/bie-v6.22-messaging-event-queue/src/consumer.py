def consumer_group(name,
                   topic_name,
                   concurrency=1):
    if concurrency < 1:
        raise ValueError("INVALID_CONCURRENCY")
    return {"name":name,
            "topic":topic_name,
            "concurrency":concurrency}

def owns_partition(record,partition):
    return partition >= 0 and record["concurrency"] >= 1
