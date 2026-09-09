def register(service_id,name,version,
             metadata=None,region=None,zone=None):
    return {"service_id":service_id,"name":name,
            "version":version,"metadata":metadata or {},
            "region":region,"zone":zone,"status":"REGISTERED"}

def registered(record):
    return record["status"]=="REGISTERED"
