SUPPORTED_DIMENSIONS = {
    "FACTUAL","CONCEPTUAL","VISUAL","AUDIO","TEMPORAL",
    "PEDAGOGICAL","OBJECTIVE_COVERAGE"
}

def correctness_check(check_id, dimension, target_ref, score,
                      evidence_refs=None, rationale=None):
    if dimension not in SUPPORTED_DIMENSIONS:
        raise ValueError("UNSUPPORTED_CORRECTNESS_DIMENSION")
    if not 0 <= score <= 1:
        raise ValueError("INVALID_CORRECTNESS_SCORE")
    return {"check_id":check_id,"dimension":dimension,
            "target_ref":target_ref,"score":score,
            "evidence_refs":evidence_refs or [],
            "rationale":rationale}

def valid(c):
    return bool(c["check_id"] and c["target_ref"]) and 0 <= c["score"] <= 1
