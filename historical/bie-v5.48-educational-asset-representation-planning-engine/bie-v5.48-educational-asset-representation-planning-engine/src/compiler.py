from selection import rank_candidates
from requirements import validate_representation

def compile_representation_plan(content_refs,objective_refs,intent,
                                candidates,requirements=None,weights=None):
    ranked=rank_candidates(candidates,weights)
    errors=[]
    selected=ranked[0] if ranked else None
    if not selected:
        errors.append("NO_REPRESENTATION_CANDIDATE")
    else:
        spec={"representation_type":selected["representation_type"]}
        errors.extend(validate_representation(spec,requirements or []))
    return {"schema_version":"5.48",
            "content_refs":content_refs,
            "objective_refs":objective_refs,
            "pedagogical_intent":intent,
            "candidates":candidates,
            "ranked_candidates":ranked,
            "selected":selected,
            "requirements":requirements or [],
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
