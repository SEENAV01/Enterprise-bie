import hashlib, json

def content_hash(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

def asset_fingerprint(asset):
    return content_hash({"kind":asset["kind"],"uri":asset["uri"],
                         "version":asset["version"],"metadata":asset.get("metadata",{})})

def same_asset(a,b):
    return asset_fingerprint(a)==asset_fingerprint(b)
