def cache_pattern(name,
                 read="CACHE_ASIDE",
                 write="WRITE_THROUGH"):
    allowed_read={"CACHE_ASIDE","READ_THROUGH"}
    allowed_write={"WRITE_THROUGH","WRITE_BEHIND","CACHE_ASIDE"}
    if read not in allowed_read or write not in allowed_write:
        raise ValueError("INVALID_CACHE_PATTERN")
    return {"name":name,"read":read,"write":write}

def supports(record,read,write):
    return record["read"]==read and record["write"]==write
