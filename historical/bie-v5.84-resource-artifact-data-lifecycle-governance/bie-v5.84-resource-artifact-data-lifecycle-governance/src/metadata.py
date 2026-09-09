def artifact_record(artifact_id,kind,created_at,
                    owner_id,policy_id,tier="HOT"):
    return {"artifact_id":artifact_id,"kind":kind,
            "created_at":created_at,"owner_id":owner_id,
            "policy_id":policy_id,"tier":tier,
            "lifecycle_state":"ACTIVE"}
