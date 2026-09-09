def speculation_guard(item):
    # Speculation is never promoted to established knowledge.
    if item.get("epistemic_status") in ("SPECULATION","HYPOTHESIS"):
        return {"allowed":False,"export_class":"REVIEW_ONLY"}
    return {"allowed":True,"export_class":"EDUCATIONAL"}
