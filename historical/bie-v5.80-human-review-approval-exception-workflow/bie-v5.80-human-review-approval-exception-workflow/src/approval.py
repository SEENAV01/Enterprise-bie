def approval_record(review_id,reviewer_id,decision,
                    rationale,artifact_id):
    return {"review_id":review_id,
            "reviewer_id":reviewer_id,
            "decision":decision,
            "rationale":rationale,
            "artifact_id":artifact_id}

def valid_decision(record):
    return record.get("decision") in {"APPROVE","REJECT"} and bool(record.get("rationale"))
