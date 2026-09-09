def validate_cache_entry(entry,input_fingerprint,
                        policy_version=None):
    if not entry: return {"valid":False,"reason":"MISS"}
    if entry.get("input_fingerprint")!=input_fingerprint:
        return {"valid":False,"reason":"INPUT_MISMATCH"}
    if policy_version is not None and entry.get("policy_version")!=policy_version:
        return {"valid":False,"reason":"POLICY_MISMATCH"}
    return {"valid":True,"reason":"MATCH"}
