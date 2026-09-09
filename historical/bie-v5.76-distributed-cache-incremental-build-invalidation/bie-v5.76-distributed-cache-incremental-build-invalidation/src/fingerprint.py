import hashlib

def fingerprint(value):
    if isinstance(value,str):
        value=value.encode()
    elif not isinstance(value,(bytes,bytearray)):
        value=json_bytes(value)
    return hashlib.sha256(value).hexdigest()

def json_bytes(value):
    import json
    return json.dumps(value,sort_keys=True,separators=(",",":")).encode()
