def service(name,version,instance_id,
            endpoint,metadata=None,weight=1):
    return {"name":name,"version":version,
            "instance_id":instance_id,
            "endpoint":endpoint,
            "metadata":metadata or {},
            "weight":weight,"status":"REGISTERED"}

def register(registry,record):
    registry.setdefault(record["name"],{})[
        record["instance_id"]]=record
    return registry

def deregister(registry,name,instance_id):
    registry.get(name,{}).pop(instance_id,None)
    return registry
