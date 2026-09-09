def version(version, etag=None, timestamp=None):
    if version < 1:
        raise ValueError("INVALID_VERSION")
    return {"version":version,"etag":etag,"timestamp":timestamp}

def matches(record, expected):
    return record["version"]==expected
