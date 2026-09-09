import hashlib

def content_id(data):
    raw=data if isinstance(data,bytes) else str(data).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def verify_content(data,expected_id):
    return content_id(data)==expected_id
