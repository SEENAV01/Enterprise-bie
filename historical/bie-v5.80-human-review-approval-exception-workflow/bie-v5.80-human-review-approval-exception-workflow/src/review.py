STATES=("QUEUED","IN_REVIEW","APPROVED","REJECTED",
        "ESCALATED","OVERRIDDEN","CLOSED")

TRANSITIONS={
 "QUEUED":{"IN_REVIEW"},
 "IN_REVIEW":{"APPROVED","REJECTED","ESCALATED","OVERRIDDEN"},
 "ESCALATED":{"IN_REVIEW","APPROVED","REJECTED"},
 "OVERRIDDEN":{"CLOSED"},
 "APPROVED":{"CLOSED"},
 "REJECTED":{"CLOSED"},
 "CLOSED":set()
}

def review_case(review_id,artifact_id,review_type,
                required_role=None,priority=0):
    return {"review_id":review_id,"artifact_id":artifact_id,
            "review_type":review_type,
            "required_role":required_role,
            "priority":priority,"state":"QUEUED",
            "annotations":[]}

def transition(case,target):
    if target not in TRANSITIONS.get(case.get("state"),set()):
        raise ValueError("INVALID_REVIEW_TRANSITION")
    out=dict(case); out["state"]=target
    return out
