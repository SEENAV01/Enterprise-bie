def source(source_id, uri, media_type="application/pdf", title=None, checksum=None):
    if not source_id or not uri:
        raise ValueError("INVALID_SOURCE")
    return {"source_id":source_id,"uri":uri,"media_type":media_type,
            "title":title,"checksum":checksum,"status":"REGISTERED"}

def valid(record):
    return record["status"]=="REGISTERED" and bool(record["uri"])
