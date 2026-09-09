def assessment_item(item_id,item_type,objective_ref,stem,
                    answer=None,choices=None,difficulty=None,
                    misconception_refs=None,metadata=None):
    return {"item_id":item_id,"item_type":item_type,
            "objective_ref":objective_ref,"stem":stem,
            "answer":answer,"choices":choices or [],
            "difficulty":difficulty,
            "misconception_refs":misconception_refs or [],
            "metadata":metadata or {}}

def item_types():
    return ["MCQ","MULTI_SELECT","NUMERICAL","SHORT_ANSWER",
            "OPEN_RESPONSE","PREDICTION","MATCHING","ORDERING",
            "PRACTICE","SCENARIO"]
