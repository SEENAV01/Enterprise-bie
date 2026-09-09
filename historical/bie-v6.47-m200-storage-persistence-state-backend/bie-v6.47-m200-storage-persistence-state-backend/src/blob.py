def blob(blob_id, content_ref, size=None,
         content_type=None, checksum=None):
    return {"blob_id":blob_id,"content_ref":content_ref,
            "size":size,"content_type":content_type,
            "checksum":checksum}

def has_checksum(record):
    return record["checksum"] is not None
