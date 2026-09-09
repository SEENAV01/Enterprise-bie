def review_checkpoint(scope,criteria,required=True):
    return {"scope":scope,"criteria":criteria,"required":required,
            "status":"PENDING","decision":None,"reviewer":None}

def record_review(checkpoint,decision,reviewer=None,notes=None):
    checkpoint["status"]="APPROVED" if decision=="APPROVE" else "CHANGES_REQUIRED"
    checkpoint["decision"]=decision
    checkpoint["reviewer"]=reviewer
    checkpoint["notes"]=notes
    return checkpoint
