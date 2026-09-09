import hashlib, json

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"))

def sha256(value):
    raw=value.encode() if isinstance(value,str) else canonical(value).encode()
    return hashlib.sha256(raw).hexdigest()
