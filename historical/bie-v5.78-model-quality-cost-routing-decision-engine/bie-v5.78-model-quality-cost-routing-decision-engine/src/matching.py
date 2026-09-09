def compatible(model,req):
    if req["capability"] not in set(model.get("capabilities",[])):
        return False
    if model.get("quality",0)<req.get("min_quality",0): return False
    if model.get("max_cost") is not None and model.get("cost_per_unit",0)>req["max_cost"]:
        return False
    if req.get("max_latency_ms") is not None and model.get("latency_ms",0)>req["max_latency_ms"]:
        return False
    if model.get("reliability",0)<req.get("min_reliability",0): return False
    cw=model.get("context_window")
    if cw is not None and cw<req.get("context_tokens",0): return False
    return True

def candidates(models,req):
    return [m for m in models if compatible(m,req)]
