def retention_policy(data_type, duration,
                    deletion_mode="DELETE",
                    legal_hold=False):
    if deletion_mode not in {"DELETE","ANONYMIZE","ARCHIVE"}:
        raise ValueError("INVALID_DELETION_MODE")
    return {"data_type":data_type,"duration":duration,
            "deletion_mode":deletion_mode,"legal_hold":legal_hold}

def deletable(record):
    return not record["legal_hold"]
