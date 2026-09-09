def diagnosis(diagnosis_id, failure_id, root_cause,
              affected_refs=None, confidence=1.0, rationale=None):
    if not root_cause:
        raise ValueError("DIAGNOSIS_REQUIRES_ROOT_CAUSE")
    return {"diagnosis_id":diagnosis_id,"failure_id":failure_id,
            "root_cause":root_cause,
            "affected_refs":affected_refs or [],
            "confidence":confidence,"rationale":rationale}

def valid(d):
    return bool(d["diagnosis_id"] and d["failure_id"] and d["root_cause"])
