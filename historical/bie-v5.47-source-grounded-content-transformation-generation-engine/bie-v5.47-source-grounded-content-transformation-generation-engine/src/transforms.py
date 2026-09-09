def transformation(transform_id,source_fragment_refs,
                   output_type,objective_refs=None,instructions=None,
                   constraints=None):
    return {"transform_id":transform_id,
            "source_fragment_refs":source_fragment_refs,
            "output_type":output_type,
            "objective_refs":objective_refs or [],
            "instructions":instructions or [],
            "constraints":constraints or {}}

def output_types():
    return ["EXPLANATION","EXAMPLE","ANALOGY","NARRATION",
            "QUESTION","ACTIVITY","VISUAL_PLAN","ASSESSMENT",
            "SUMMARY","STUDY_GUIDE"]
