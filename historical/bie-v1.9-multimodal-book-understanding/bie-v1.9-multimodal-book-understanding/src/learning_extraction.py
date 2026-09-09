QUESTION_TYPES=["what","why","how","when","where","who","derivation","application"]

def empty_matrix():
    return {k:[] for k in QUESTION_TYPES}

def add_question(matrix,kind,qid):
    if kind in matrix and qid not in matrix[kind]:
        matrix[kind].append(qid)

def infer_visual_learning_roles(assets):
    roles=[]
    for a in assets:
        t=a.get("type")
        if t=="figure": roles.append({"asset_ref":a["asset_ref"],"role":"process_or_system_visual"})
        elif t=="table": roles.append({"asset_ref":a["asset_ref"],"role":"comparison_or_data_evidence"})
        elif t=="equation": roles.append({"asset_ref":a["asset_ref"],"role":"quantitative_relationship"})
    return roles
