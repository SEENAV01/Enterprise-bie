from identity import artifact_id

def put(store,data,metadata=None):
    key=artifact_id(data)
    if key not in store:
        store[key]={"bytes":data,"metadata":metadata or {}}
    return key

def get(store,key):
    return store.get(key)

def contains(store,key):
    return key in store
