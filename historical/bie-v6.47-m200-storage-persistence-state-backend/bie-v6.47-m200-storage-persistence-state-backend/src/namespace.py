def namespace(namespace_id, name,
             isolation="DEFAULT", metadata=None):
    return {"namespace_id":namespace_id,"name":name,
            "isolation":isolation,"metadata":metadata or {},
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
