import hashlib, json

def cache_key(composition_id, inputs):
    raw=json.dumps({"composition_id":composition_id,"inputs":inputs},sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()

def lookup(cache, key):
    return cache.get(key)

def store(cache, key, artifact):
    cache[key]=artifact
    return artifact
