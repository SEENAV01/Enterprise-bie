def request_approval(run_id, approver_role="release_manager"):
    return {"run_id":run_id,"status":"PENDING","approver_role":approver_role,"decision":None}

def decide(request, decision, actor, comment=None):
    if decision not in {"APPROVE","REJECT"}:
        return {"ok":False,"error":"INVALID_DECISION","request":request}
    request.update({"status":"DECIDED","decision":decision,"actor":actor,"comment":comment})
    return {"ok":True,"request":request}
