def representation(rep_id,rep_type,concept_refs=None,
                     purpose=None,priority=1.0):
    return {"rep_id":rep_id,"rep_type":rep_type,
            "concept_refs":concept_refs or [],
            "purpose":purpose,"priority":priority}

def representation_types():
    return ["NARRATION","TEXT","DIAGRAM","ILLUSTRATION","ANIMATION",
            "EQUATION","SIMULATION","TABLE","COMPARISON","ANALOGY",
            "INTERACTION"]
