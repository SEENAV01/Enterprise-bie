def object_identity(object_id,bucket,key,
                    version=None):
    return {"object_id":object_id,"bucket":bucket,
            "key":key,"version":version,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
