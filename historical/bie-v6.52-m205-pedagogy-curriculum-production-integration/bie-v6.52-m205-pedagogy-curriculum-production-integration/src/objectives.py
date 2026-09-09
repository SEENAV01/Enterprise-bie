def objective(objective_id, label, level, evidence_ids=None):
    if not objective_id or not label:
        raise ValueError("INVALID_OBJECTIVE")
    return {"objective_id": objective_id, "label": label, "level": level,
            "evidence_ids": evidence_ids or []}

def valid(obj):
    return bool(obj["objective_id"] and obj["label"] and obj["level"])
