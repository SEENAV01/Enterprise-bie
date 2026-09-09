def dual_control(decisions):
    reviewers={d.get("reviewer_id") for d in decisions}
    approvals=[d for d in decisions if d.get("decision")=="APPROVE"]
    return len(reviewers)>=2 and len(approvals)>=2

def conflict(decisions):
    values={d.get("decision") for d in decisions}
    return "APPROVE" in values and "REJECT" in values
