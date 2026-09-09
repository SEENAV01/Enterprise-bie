from lesson_plan import generate_lesson_plan,validate_plan
from objectives import valid_bloom

def build_objective_runtime():
    concepts=[{"concept_id":"c1","title":"electric charge"},
              {"concept_id":"c2","title":"electric field"}]
    plan=generate_lesson_plan("s1-L1",concepts,["explain"])
    bloom_valid=all(valid_bloom(o["bloom"]) for o in plan["objectives"])
    validation=validate_plan(plan)
    return {"schema_version":"6.76","lesson_id":"s1-L1",
            "concepts":concepts,"lesson_plan":plan,
            "validation":validation,
            "objective_gate":{"valid":bloom_valid and validation["passed"],"errors":[]}}
