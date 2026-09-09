def object_ref(object_id,bucket,key,
               tenant_id=None,version=None):
    return {"object_id":object_id,
            "bucket":bucket,
            "key":key,
            "tenant_id":tenant_id,
            "version":version}

def tenant_matches(record,tenant_id):
    return record["tenant_id"] in {None,tenant_id}
