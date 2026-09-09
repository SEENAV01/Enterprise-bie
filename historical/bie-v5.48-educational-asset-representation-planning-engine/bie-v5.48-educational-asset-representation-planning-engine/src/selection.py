def representation_candidate(candidate_id,representation_type,
                              signals=None,constraints=None):
    return {"candidate_id":candidate_id,
            "representation_type":representation_type,
            "signals":signals or {},
            "constraints":constraints or {}}

def score_candidate(candidate,weights=None):
    weights=weights or {}
    return sum(v*weights.get(k,1.0)
               for k,v in candidate.get("signals",{}).items()
               if isinstance(v,(int,float)))

def rank_candidates(candidates,weights=None):
    scored=[(score_candidate(c,weights),c) for c in candidates]
    return [c for _,c in sorted(scored,key=lambda x:x[0],reverse=True)]
