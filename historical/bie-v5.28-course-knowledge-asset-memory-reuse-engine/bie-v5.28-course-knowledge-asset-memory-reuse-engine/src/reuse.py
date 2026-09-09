def reuse_candidate(record_id,score,reason,
                    adaptation_required=False):
    return {"record_id":record_id,"score":score,"reason":reason,
            "adaptation_required":adaptation_required}

def rank_candidates(candidates):
    return sorted(candidates,key=lambda x:x.get("score",0),reverse=True)

def reuse_policy(candidate,threshold=0.85):
    if candidate.get("score",0)>=threshold:
        return "REUSE"
    if candidate.get("score",0)>=threshold-0.15:
        return "ADAPT"
    return "REGENERATE"
