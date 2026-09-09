def register(registry,event_type,version,schema):
    registry.setdefault(event_type,{})[version]=schema
    return {"event_type":event_type,"version":version}

def get(registry,event_type,version):
    return registry.get(event_type,{}).get(version)

def versions(registry,event_type):
    return sorted(registry.get(event_type,{}))
