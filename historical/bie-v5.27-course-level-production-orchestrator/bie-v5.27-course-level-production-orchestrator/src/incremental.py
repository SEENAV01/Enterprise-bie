import hashlib,json

def artifact_fingerprint(spec):
    raw=json.dumps(spec,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def needs_rebuild(previous_fingerprint,current_spec):
    return previous_fingerprint!=artifact_fingerprint(current_spec)
