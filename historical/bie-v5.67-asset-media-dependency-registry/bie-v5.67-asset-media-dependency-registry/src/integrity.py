import hashlib

def content_hash(data):
    if isinstance(data,str): data=data.encode()
    return hashlib.sha256(data).hexdigest()

def verify_hash(data,expected):
    return content_hash(data)==expected
