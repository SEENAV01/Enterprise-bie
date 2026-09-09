def misconception(misconception_id,concept_ref,description,
                  evidence=None,severity=None):
    return {"misconception_id":misconception_id,
            "concept_ref":concept_ref,"description":description,
            "evidence":evidence or [],"severity":severity}

def diagnose_from_item(item,response_correct):
    if response_correct is True:
        return []
    return item.get("misconception_refs",[])
