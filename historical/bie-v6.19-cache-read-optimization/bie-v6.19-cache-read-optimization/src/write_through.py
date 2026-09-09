def write_through(cache,key,
                  writer):
    return {"cache":cache,
            "key":key,
            "pattern":"WRITE_THROUGH",
            "writer":writer}

def write(record):
    return {"action":"WRITE_BACKING_STORE_AND_CACHE",
            "cache":record["cache"],
            "key":record["key"],
            "writer":record["writer"]}
