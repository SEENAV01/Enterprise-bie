def cache_key(asset_type,inputs,versions,parameters=None):
    import hashlib,json
    payload={"asset_type":asset_type,"inputs":inputs,
             "versions":versions,"parameters":parameters or {}}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def cache_record(key,artifact_ref,status="VALID"):
    return {"cache_key":key,"artifact_ref":artifact_ref,"status":status}
