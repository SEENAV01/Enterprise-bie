import hashlib,json

def build_fingerprint(spec):
    raw=json.dumps(spec,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def cache_key(project_id,composition_id,fingerprint):
    return f"{project_id}:{composition_id}:{fingerprint}"
