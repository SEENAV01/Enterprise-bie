import hashlib, json

def stable_identity(namespace,payload):
    body=json.dumps(payload,sort_keys=True,separators=(",",":"),
                   ensure_ascii=False).encode()
    return namespace+":"+hashlib.sha256(body).hexdigest()[:24]

def artifact_identity(artifact):
    return stable_identity("artifact",artifact)

def build_identity(manifest):
    return stable_identity("build",manifest)
