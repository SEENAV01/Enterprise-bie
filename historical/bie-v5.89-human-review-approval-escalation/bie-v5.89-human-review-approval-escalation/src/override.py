def override_request(item_id,original_decision,
                    requested_decision,requester,reason):
    return {"item_id":item_id,
            "original_decision":original_decision,
            "requested_decision":requested_decision,
            "requester":requester,"reason":reason,
            "status":"PENDING_APPROVAL"}

def approve_override(record,approver):
    out=dict(record); out["approver"]=approver
    out["status"]="APPROVED"
    return out
