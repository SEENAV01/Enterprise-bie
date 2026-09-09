def object_metadata(object_id,
                   content_type,
                   size,
                   checksum_ref=None,
                   custom=None):
    return {"object_id":object_id,
            "content_type":content_type,
            "size":size,
            "checksum_ref":checksum_ref,
            "custom":custom or {}}

def has_checksum(record):
    return bool(record["checksum_ref"])
