def match_models(models, required_capability):
    return [m for m in models if m["status"]=="ACTIVE" and
            required_capability in m["capabilities"]]

def route(models, capability, max_cost=None, preferred_provider=None):
    candidates=match_models(models,capability)
    if max_cost is not None:
        candidates=[m for m in candidates if m["cost_per_unit"]<=max_cost]
    if preferred_provider:
        preferred=[m for m in candidates if m["provider"]==preferred_provider]
        if preferred: candidates=preferred
    return min(candidates,key=lambda m:m["cost_per_unit"]) if candidates else None
