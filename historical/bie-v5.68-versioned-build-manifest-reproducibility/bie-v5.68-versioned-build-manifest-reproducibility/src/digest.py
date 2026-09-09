import hashlib,json

def canonical_json(value):
    return json.dumps(value,sort_keys=True,
                      separators=(",",":"),ensure_ascii=False)

def manifest_digest(manifest):
    return hashlib.sha256(
        canonical_json(manifest).encode("utf-8")
    ).hexdigest()

def artifact_identity(manifest):
    return f"{manifest.get('build_id')}:{manifest_digest(manifest)}"
