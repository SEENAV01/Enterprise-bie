def persist(instance, store):
    store[instance["workflow_id"]]=dict(instance)
    return {"ok":True,"workflow_id":instance["workflow_id"]}

def resume(workflow_id, store):
    item=store.get(workflow_id)
    if not item: return {"ok":False,"error":"WORKFLOW_NOT_FOUND"}
    return {"ok":True,"instance":item}
