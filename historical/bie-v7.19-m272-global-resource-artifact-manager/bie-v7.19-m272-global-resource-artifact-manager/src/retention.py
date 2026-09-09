def retention_decision(artifact, now, pinned=False):
    if pinned:return {"retain":True,"reason":"PINNED"}
    expiry=artifact.get("metadata",{}).get("expires_at")
    if expiry is not None and now>=expiry:
        return {"retain":False,"reason":"EXPIRED"}
    return {"retain":True,"reason":"ACTIVE"}

def garbage_candidates(store, now):
    return [a for a in store.values() if not retention_decision(a,now)["retain"]]
