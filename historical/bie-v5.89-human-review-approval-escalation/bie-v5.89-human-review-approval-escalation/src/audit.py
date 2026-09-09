def review_audit(item_id,event,actor,
                decision=None,evidence_refs=None):
    return {"item_id":item_id,"event":event,
            "actor":actor,"decision":decision,
            "evidence_refs":evidence_refs or {}}
