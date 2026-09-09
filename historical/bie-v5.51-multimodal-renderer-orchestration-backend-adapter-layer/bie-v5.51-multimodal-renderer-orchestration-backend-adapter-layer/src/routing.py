from capability import capability_match,constraint_match

def route_candidates(contract,backends):
    candidates=[]
    for b in backends:
        if capability_match(contract,b) and constraint_match(contract,b):
            candidates.append(b)
    return candidates

def score_backend(contract,backend,signals=None,weights=None):
    signals=signals or {}
    weights=weights or {}
    return sum(v*weights.get(k,1.0) for k,v in signals.items()
               if isinstance(v,(int,float)))

def choose_backend(contract,backends,signals=None,weights=None):
    candidates=route_candidates(contract,backends)
    ranked=sorted(candidates,
                  key=lambda b:score_backend(contract,b,signals,weights),
                  reverse=True)
    return ranked[0] if ranked else None
