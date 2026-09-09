def ground_claim(claim,evidence_items):
    matches=[e for e in evidence_items if claim["claim_id"] in e.get("claim_ids",[])]
    best=max([e.get("relevance",0) for e in matches],default=0)
    return {"claim_id":claim["claim_id"],"evidence_ids":[e["evidence_id"] for e in matches],
            "grounded":bool(matches),"best_relevance":best}
def grounding_coverage(claims,grounded):
    ids={g["claim_id"] for g in grounded if g["grounded"]}
    return len(ids)/len(claims) if claims else 1.0
