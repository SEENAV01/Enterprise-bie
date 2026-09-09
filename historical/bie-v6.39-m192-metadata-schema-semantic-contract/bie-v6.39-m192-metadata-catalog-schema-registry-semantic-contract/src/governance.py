def schema_governance(schema_id, owner,
                     approval_required=True,
                     compatibility="BACKWARD"):
    return {"schema_id":schema_id,"owner":owner,
            "approval_required":approval_required,
            "compatibility":compatibility}

def approval_required(record):
    return record["approval_required"]
