from matching import candidates
from scoring import rank
from fallback import fallback_chain

def route(models,requirements,weights=None,
          budget=None):
    cs=candidates(models,requirements)
    if budget is not None:
        cs=[m for m in cs if m.get("cost_per_unit",0)<=budget]
    ranked=rank(cs,weights)
    if not ranked:
        return {"status":"NO_COMPATIBLE_MODEL",
                "candidates":[]}
    chain=fallback_chain(ranked,ranked[0]["model_id"])
    return {"status":"ROUTED",
            "primary":ranked[0]["model_id"],
            "fallback_chain":chain,
            "ranked":[m["model_id"] for m in ranked]}
