from distractors import validate_distractors

def compile_assessment(items,rules=None,evidence=None):
    errors=[]
    for item in items:
        if item.get("item_type")=="MCQ":
            errors.extend(validate_distractors(item.get("choices",[]),
                                               item.get("answer")))
        if not item.get("objective_ref"):
            errors.append("OBJECTIVE_REFERENCE_MISSING")
    return {"schema_version":"5.42",
            "items":items,"evaluation_rules":rules or [],
            "evidence":evidence or [],
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
