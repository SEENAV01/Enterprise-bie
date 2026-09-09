def change_request(request_id,policy_id,
                  from_version,to_version,
                  author,reason,approval_required=True):
    return {"request_id":request_id,
            "policy_id":policy_id,
            "from_version":from_version,
            "to_version":to_version,
            "author":author,"reason":reason,
            "approval_required":approval_required,
            "status":"PENDING"}

def approve(request,approver):
    out=dict(request)
    out["status"]="APPROVED"
    out["approver"]=approver
    return out
