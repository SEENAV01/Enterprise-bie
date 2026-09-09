def rotation_record(rotation_id,secret_or_credential,
                   old_version,new_version,
                   rotated_at,status="COMPLETED"):
    return {"rotation_id":rotation_id,
            "subject":secret_or_credential,
            "old_version":old_version,
            "new_version":new_version,
            "rotated_at":rotated_at,
            "status":status}
