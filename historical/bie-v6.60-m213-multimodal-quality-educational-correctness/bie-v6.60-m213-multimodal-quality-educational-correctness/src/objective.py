def objective_coverage(objective_id, objective_text,
                      covered, coverage_score, scene_refs=None,
                      evidence_refs=None):
    if not 0 <= coverage_score <= 1:
        raise ValueError("INVALID_COVERAGE_SCORE")
    return {"objective_id":objective_id,"objective_text":objective_text,
            "covered":covered,"coverage_score":coverage_score,
            "scene_refs":scene_refs or [],
            "evidence_refs":evidence_refs or []}

def valid(o):
    return bool(o["objective_id"] and o["objective_text"]) and 0 <= o["coverage_score"] <= 1
