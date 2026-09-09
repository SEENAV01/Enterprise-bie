DECISIONS={"APPROVE","REJECT","ESCALATE","REQUEST_CHANGES"}

def review_decision(item_id,reviewer_id,decision,
                    rationale,evidence_refs=None):
    if decision not in DECISIONS:
        raise ValueError("INVALID_REVIEW_DECISION")
    return {"item_id":item_id,"reviewer_id":reviewer_id,
            "decision":decision,"rationale":rationale,
            "evidence_refs":evidence_refs or {}}

def terminal(decision):
    return decision in {"APPROVE","REJECT"}
