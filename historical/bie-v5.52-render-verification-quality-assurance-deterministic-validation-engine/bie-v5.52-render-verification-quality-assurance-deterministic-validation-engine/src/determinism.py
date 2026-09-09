import hashlib, json

def artifact_fingerprint(artifact_metadata):
    payload=json.dumps(artifact_metadata,sort_keys=True,
                       separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

def compare_fingerprints(expected,actual):
    return {"match":expected==actual,
            "expected":expected,"actual":actual}
