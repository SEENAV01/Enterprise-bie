def collection(collection_id, namespace,
              schema_ref=None, indexes=None):
    return {"collection_id":collection_id,"namespace":namespace,
            "schema_ref":schema_ref,"indexes":indexes or [],
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
