def citation_map(claims,evidence_by_id):
    return [{"claim_id":c["claim_id"],
             "evidence":[evidence_by_id[e] for e in c.get("evidence_ids",[]) if e in evidence_by_id]}
            for c in claims]

def coverage(claims,evidence_by_id):
    grounded=sum(bool(c.get("evidence_ids")) and
                 all(e in evidence_by_id for e in c["evidence_ids"]) for c in claims)
    return {"claims":len(claims),"grounded_claims":grounded,
            "coverage":grounded/len(claims) if claims else 1.0}
