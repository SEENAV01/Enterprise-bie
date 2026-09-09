def approval_request(request_id,operation,requester,
                    approvers_required=1,reason=None):
    return {"request_id":request_id,"operation":operation,
            "requester":requester,
            "approvers_required":approvers_required,
            "reason":reason,"approvals":[],"status":"PENDING"}

def add_approval(record,approver,decision,comment=None):
    out=dict(record); out["approvals"]=list(record.get("approvals",[]))
    out["approvals"].append({"approver":approver,
                             "decision":decision,"comment":comment})
    accepted=sum(x["decision"]=="APPROVE" for x in out["approvals"])
    rejected=any(x["decision"]=="REJECT" for x in out["approvals"])
    if rejected: out["status"]="REJECTED"
    elif accepted>=out["approvers_required"]: out["status"]="APPROVED"
    return out
