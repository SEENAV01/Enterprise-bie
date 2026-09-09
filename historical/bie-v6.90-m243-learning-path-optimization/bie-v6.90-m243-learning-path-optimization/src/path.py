from sequencing import optimize_sequence
from load import cognitive_load,validate_load
from granularity import estimate_granularity,validate_granularity

def build_learning_path(units,prerequisite_map):
    seq=optimize_sequence(units,prerequisite_map)
    ordered=[next(u for u in units if u["concept_id"]==c) for c in seq["order"]]
    checks=[]
    for u in ordered:
        checks.append({"concept_id":u["concept_id"],
                       "load":cognitive_load(u),
                       "load_validation":validate_load(cognitive_load(u)),
                       "granularity":estimate_granularity(u),
                       "granularity_validation":validate_granularity(estimate_granularity(u))})
    valid=seq["valid"] and all(x["load_validation"]["passed"] and x["granularity_validation"]["passed"] for x in checks)
    return {"sequence":seq,"units":ordered,"checks":checks,"valid":valid}
