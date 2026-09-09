def read_through(cache,key,
                 loader):
    return {"cache":cache,
            "key":key,
            "pattern":"READ_THROUGH",
            "loader":loader}

def miss(record):
    return {"action":"LOAD_AND_POPULATE",
            "cache":record["cache"],
            "key":record["key"],
            "loader":record["loader"]}
