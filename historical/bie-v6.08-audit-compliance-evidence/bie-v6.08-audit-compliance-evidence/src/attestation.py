def attestation(attestation_id,
                 control_id,reviewer,
                 status,reviewed_at,
                 evidence_refs=None,
                 notes=None):
    return {"attestation_id":attestation_id,
            "control_id":control_id,
            "reviewer":reviewer,
            "status":status,
            "reviewed_at":reviewed_at,
            "evidence_refs":evidence_refs or [],
            "notes":notes}

def accepted(record):
    return record.get("status")=="PASS"
