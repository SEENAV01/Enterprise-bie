def approval_gate(gate_id,
                 workflow_id,
                 approvers,
                 required=1):
    return {"gate_id":gate_id,
            "workflow_id":workflow_id,
            "approvers":approvers,
            "required":required,
            "approved_by":[],
            "status":"PENDING"}

def approve(record,actor):
    out=dict(record)
    if actor not in out["approved_by"]:
        out["approved_by"]=list(out["approved_by"])+[actor]
    if len(out["approved_by"])>=out["required"]:
        out["status"]="APPROVED"
    return out
