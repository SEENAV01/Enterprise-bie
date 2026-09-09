def worked_example(example_id,concept_id,problem,steps,final_answer,
                   difficulty="FOUNDATION"):
    return {"example_id":example_id,"concept_id":concept_id,"problem":problem,
            "steps":steps,"final_answer":final_answer,"difficulty":difficulty}

def validate_example(example):
    errors=[]
    if not example.get("problem"): errors.append("MISSING_PROBLEM")
    if not example.get("steps"): errors.append("MISSING_STEPS")
    if example.get("final_answer") is None: errors.append("MISSING_FINAL_ANSWER")
    return {"passed":not errors,"errors":errors}
