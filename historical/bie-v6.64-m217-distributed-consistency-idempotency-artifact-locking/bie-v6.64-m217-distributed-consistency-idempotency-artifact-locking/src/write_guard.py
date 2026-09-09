def guarded_write(lock_manager, fencing, artifact_id,
                  owner, token, payload):
    if lock_manager.owner(artifact_id) != owner:
        raise ValueError("LOCK_NOT_HELD")
    if not fencing.valid(artifact_id, token):
        raise ValueError("STALE_FENCING_TOKEN")
    return {"artifact_id":artifact_id,"owner":owner,
            "fencing_token":token,"payload":payload}
