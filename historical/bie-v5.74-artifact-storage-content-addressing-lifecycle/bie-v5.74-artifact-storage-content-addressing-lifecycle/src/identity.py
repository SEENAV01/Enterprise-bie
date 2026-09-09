import hashlib

def content_hash(data):
    if isinstance(data,str): data=data.encode()
    return hashlib.sha256(data).hexdigest()

def artifact_id(data):
    return "sha256:"+content_hash(data)
