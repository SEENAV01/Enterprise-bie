def checksum(algorithm,value):
    if algorithm not in {"SHA256","SHA512","MD5"}:
        raise ValueError("INVALID_CHECKSUM_ALGORITHM")
    return {"algorithm":algorithm,"value":value}

def matches(record,expected):
    return record["value"]==expected
