from evidence import evidence_weight

def aggregate_objective_evidence(events,objective_ref):
    selected=[e for e in events if e.get("objective_ref")==objective_ref]
    weights=[evidence_weight(e) for e in selected]
    scores=[e.get("score") for e in selected
            if isinstance(e.get("score"),(int,float))]
    weighted_score=None
    if scores:
        pairs=[(evidence_weight(e),e["score"]) for e in selected
               if isinstance(e.get("score"),(int,float))]
        total=sum(w for w,_ in pairs)
        weighted_score=sum(w*s for w,s in pairs)/total if total else None
    return {"objective_ref":objective_ref,
            "evidence_count":len(selected),
            "weighted_score":weighted_score,
            "total_weight":sum(weights)}
