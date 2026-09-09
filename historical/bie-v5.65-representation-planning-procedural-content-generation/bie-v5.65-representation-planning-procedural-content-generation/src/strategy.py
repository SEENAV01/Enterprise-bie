def generation_strategy(strategy_id,modality,
                       generator_type,template=None,
                       parameters=None,validation=None):
    return {"strategy_id":strategy_id,"modality":modality,
            "generator_type":generator_type,"template":template,
            "parameters":parameters or {},
            "validation":validation or {}}

def select_strategy(spec,strategies):
    candidates=[s for s in strategies if s.get("modality")==spec.get("modality")]
    if not candidates: raise ValueError("NO_GENERATION_STRATEGY")
    return candidates[0]
