def compare_claims(claims):
    groups={}
    for c in claims:
        key=c.get("concept_refs") and c["concept_refs"][0] or c["claim_id"]
        groups.setdefault(key,[]).append(c)
    return groups

def contradiction_pair(claim_a,claim_b,reason=None):
    return {"claim_a":claim_a["claim_id"],"claim_b":claim_b["claim_id"],
            "relation":"CONTRADICTS","reason":reason}

def reconcile_claim(claim_id,evidence_items,decision,
                    confidence=None,uncertainty=None):
    return {"claim_id":claim_id,"decision":decision,
            "confidence":confidence,"uncertainty":uncertainty,
            "evidence_ids":[e["evidence_id"] for e in evidence_items]}
