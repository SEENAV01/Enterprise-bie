import hashlib
def content_id(data: bytes):
    return "sha256:"+hashlib.sha256(data).hexdigest()
def artifact_id(namespace,name,version):
    return f"{namespace}:{name}:{version}"
