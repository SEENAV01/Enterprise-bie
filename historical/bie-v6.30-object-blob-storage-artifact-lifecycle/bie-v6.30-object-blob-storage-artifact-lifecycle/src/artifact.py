def artifact(object_id,
            artifact_type,
            source=None,
            manifest=None):
    return {"object_id":object_id,
            "artifact_type":artifact_type,
            "source":source,
            "manifest":manifest or {},
            "status":"AVAILABLE"}

def available(record):
    return record["status"]=="AVAILABLE"
