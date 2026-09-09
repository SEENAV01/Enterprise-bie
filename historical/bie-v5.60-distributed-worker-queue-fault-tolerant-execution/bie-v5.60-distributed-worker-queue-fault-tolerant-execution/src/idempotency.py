def execution_key(job_id,input_versions=None,
                  parameters=None):
    import hashlib,json
    payload={"job_id":job_id,
             "input_versions":input_versions or {},
             "parameters":parameters or {}}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def already_completed(key,completed_keys):
    return key in set(completed_keys)
