def upload_request(upload_id,
                  object_id,
                  content_type,
                  size=None,
                  multipart=False):
    if size is not None and size < 0:
        raise ValueError("INVALID_SIZE")
    return {"upload_id":upload_id,
            "object_id":object_id,
            "content_type":content_type,
            "size":size,
            "multipart":multipart,
            "status":"REQUESTED"}

def start(record):
    out=dict(record); out["status"]="IN_PROGRESS"; return out

def complete(record):
    out=dict(record); out["status"]="COMPLETED"; return out
