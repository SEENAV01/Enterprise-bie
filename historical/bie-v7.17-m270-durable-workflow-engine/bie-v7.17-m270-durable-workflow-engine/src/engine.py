def start(defn, workflow_id, context=None):
    return {"workflow_id":workflow_id,"definition_id":defn["workflow_id"],
            "state":defn["initial"],"status":"RUNNING",
            "context":context or {},"history":[]}

def transition(defn, instance, event, payload=None):
    key=f"{instance['state']}:{event}"
    target=defn["transitions"].get(key)
    if not target:
        return {"ok":False,"error":"TRANSITION_NOT_ALLOWED","instance":instance}
    instance["history"].append({"from":instance["state"],"event":event,"to":target})
    instance["state"]=target
    instance["context"].update(payload or {})
    if target in {"COMPLETED","FAILED","CANCELLED"}:
        instance["status"]="TERMINAL"
    return {"ok":True,"instance":instance}
