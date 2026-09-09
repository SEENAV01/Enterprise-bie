def assessment(assessment_id, kind, objective_ids,
                success_criteria=None, evidence_ids=None):
    if not objective_ids:
        raise ValueError("ASSESSMENT_REQUIRES_OBJECTIVES")
    return {"assessment_id": assessment_id, "kind": kind,
            "objective_ids": objective_ids,
            "success_criteria": success_criteria or [],
            "evidence_ids": evidence_ids or []}

def aligned(item):
    return bool(item["objective_ids"]) and bool(item["success_criteria"])
