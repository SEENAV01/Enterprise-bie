def assessment_item(item_id,objective_id,item_type,prompt,
                    answer=None,difficulty="MEDIUM",choices=None):
    return {"item_id":item_id,"objective_id":objective_id,"item_type":item_type,
            "prompt":prompt,"answer":answer,"difficulty":difficulty,
            "choices":choices or []}

def validate_item(item):
    errors=[]
    if not item.get("item_id") or not item.get("objective_id"): errors.append("MISSING_ID")
    if not item.get("prompt"): errors.append("MISSING_PROMPT")
    if item.get("item_type")=="MCQ" and len(item.get("choices",[]))<2:
        errors.append("INSUFFICIENT_CHOICES")
    return {"passed":not errors,"errors":errors}
