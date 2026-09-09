def multipart_upload(upload_id,
                    object_key,
                    part_size,
                    total_parts):
    if part_size < 1 or total_parts < 1:
        raise ValueError("INVALID_MULTIPART")
    return {"upload_id":upload_id,
            "object_key":object_key,
            "part_size":part_size,
            "total_parts":total_parts,
            "status":"INITIATED"}

def complete(record,parts):
    return len(parts)==record["total_parts"]
