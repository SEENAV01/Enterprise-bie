import hashlib,json

def content_hash(payload):
    raw=json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def cache_key(asset_record, transformation):
    return content_hash({"asset":asset_record,"transformation":transformation})

def cache_entry(key, output_ref):
    return {"cache_key":key,"output_ref":output_ref,"status":"READY"}
