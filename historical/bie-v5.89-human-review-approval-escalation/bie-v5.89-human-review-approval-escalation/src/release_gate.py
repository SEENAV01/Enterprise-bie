def review_release_gate(automated_pass,decision):
    human=decision["decision"]
    if human=="APPROVE":
        return {"eligible":bool(automated_pass),
                "reason":"HUMAN_APPROVED"}
    if human=="REJECT":
        return {"eligible":False,"reason":"HUMAN_REJECTED"}
    if human in {"ESCALATE","REQUEST_CHANGES"}:
        return {"eligible":False,"reason":human}
    return {"eligible":False,"reason":"UNKNOWN"}
