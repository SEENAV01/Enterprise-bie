def multipart_upload(upload_id,
                    object_id,
                    part_size,
                    total_parts):
    if part_size <= 0 or total_parts <= 0:
        raise ValueError("INVALID_MULTIPART")
    return {"upload_id":upload_id,
            "object_id":object_id,
            "part_size":part_size,
            "total_parts":total_parts,
            "parts":{},
            "status":"OPEN"}

def add_part(record,part_number,checksum):
    if not 1 <= part_number <= record["total_parts"]:
        raise ValueError("INVALID_PART_NUMBER")
    out=dict(record)
    out["parts"]=dict(record["parts"])
    out["parts"][part_number]=checksum
    return out

def ready(record):
    return len(record["parts"]) == record["total_parts"]
