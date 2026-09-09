def formula_record(formula_id,source_region,latex=None,
                   text=None,confidence=None):
    return {"formula_id":formula_id,"source_region":source_region,
            "latex":latex,"text":text,"confidence":confidence}

def formula_gate(formula,minimum_confidence=0.8):
    return {"valid":formula.get("confidence",0)>=minimum_confidence,
            "review_required":formula.get("confidence",0)<minimum_confidence}
