def commit_record(commit_id, artifact_id, owner,
                  idempotency_key, fencing_token, checksum):
    return {"commit_id":commit_id,"artifact_id":artifact_id,
            "owner":owner,"idempotency_key":idempotency_key,
            "fencing_token":fencing_token,"checksum":checksum}

def valid(c):
    return all(c.get(k) for k in
               ("commit_id","artifact_id","owner",
                "idempotency_key","checksum"))
