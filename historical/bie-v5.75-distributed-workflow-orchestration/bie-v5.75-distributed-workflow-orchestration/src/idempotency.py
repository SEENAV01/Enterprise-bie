def idempotency_key(job_id,input_hash,policy_version):
    return f"{job_id}:{input_hash}:{policy_version}"

def already_completed(completed_keys,key):
    return key in set(completed_keys)
