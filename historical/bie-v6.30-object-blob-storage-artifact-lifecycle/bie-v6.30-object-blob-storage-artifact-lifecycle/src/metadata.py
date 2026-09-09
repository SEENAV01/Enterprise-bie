def metadata(content_type=None,
             size=None,custom=None):
    if size is not None and size < 0:
        raise ValueError("INVALID_SIZE")
    return {"content_type":content_type,
            "size":size,"custom":custom or {}}

def valid(record):
    return record["size"] is None or record["size"] >= 0
