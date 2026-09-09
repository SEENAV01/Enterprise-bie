SUPPORTED_STRATEGIES = {
    "EXPLANATION", "EXAMPLE", "DEMONSTRATION", "GUIDED_PRACTICE",
    "RETRIEVAL", "SPACED_REVIEW", "COMPARISON", "MISCONCEPTION_REPAIR"
}

def strategy(strategy_id, name, objective_ids=None, rationale=None):
    if name not in SUPPORTED_STRATEGIES:
        raise ValueError("UNSUPPORTED_PEDAGOGY_STRATEGY")
    return {"strategy_id": strategy_id, "name": name,
            "objective_ids": objective_ids or [], "rationale": rationale}

def valid(item):
    return item["name"] in SUPPORTED_STRATEGIES and bool(item["objective_ids"])
