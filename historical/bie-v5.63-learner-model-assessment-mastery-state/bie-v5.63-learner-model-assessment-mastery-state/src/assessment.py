def assessment_item(item_id,item_type,concept_refs,
                   objective_refs=None,difficulty=None,
                   rubric=None,misconception_refs=None):
    return {"item_id":item_id,"item_type":item_type,
            "concept_refs":concept_refs,
            "objective_refs":objective_refs or [],
            "difficulty":difficulty,"rubric":rubric or {},
            "misconception_refs":misconception_refs or []}

def assess_response(item,response,score,confidence=None):
    return {"item_id":item["item_id"],"response":response,
            "score":score,"confidence":confidence,
            "concept_refs":item["concept_refs"],
            "objective_refs":item.get("objective_refs",[])}
