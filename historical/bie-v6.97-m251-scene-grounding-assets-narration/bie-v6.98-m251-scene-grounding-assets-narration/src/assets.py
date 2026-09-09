def rank_asset_candidates(candidates, required_type, concept_tags=None):
    concept_tags=set(concept_tags or [])
    ranked=[]
    for c in candidates:
        score=0
        if c.get("type")==required_type: score+=0.5
        score+=0.5*len(concept_tags.intersection(set(c.get("tags",[]))))/max(1,len(concept_tags))
        ranked.append({**c,"grounding_score":round(score,3)})
    return sorted(ranked,key=lambda x:x["grounding_score"],reverse=True)

def select_asset(candidates, threshold=0.5):
    return next((c for c in candidates if c["grounding_score"]>=threshold),None)
