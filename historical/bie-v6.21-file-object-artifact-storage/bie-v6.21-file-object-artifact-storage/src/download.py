def download_request(object_id,
                    version=None,
                    byte_range=None):
    return {"object_id":object_id,
            "version":version,
            "byte_range":byte_range,
            "status":"REQUESTED"}

def ranged(record):
    return record["byte_range"] is not None
