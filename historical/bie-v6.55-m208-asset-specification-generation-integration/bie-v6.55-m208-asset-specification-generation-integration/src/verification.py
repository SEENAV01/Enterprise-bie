def verification(check_id, target_id, status,
                 evidence_ids=None, notes=None):
    if status not in {"PASS", "FAIL", "REVIEW"}:
        raise ValueError("INVALID_VERIFICATION_STATUS")
    return {
        "check_id": check_id, "target_id": target_id,
        "status": status, "evidence_ids": evidence_ids or [],
        "notes": notes
    }

def passed(v):
    return v["status"] == "PASS"
