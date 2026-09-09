def assess_claim(c,evidence_index):
    ids=c.get("evidence_ids",[])
    if c.get("claim_type") in ("DERIVED","INFERRED","ENRICHMENT"):
        return {"status":"SUPPORTED_BY_REASONING" if c.get("reasoning_notes")
                else "REASONING_REQUIRED"}
    if not ids:
        return {"status":"UNSUPPORTED"}
    missing=[i for i in ids if i not in evidence_index]
    if missing: return {"status":"MISSING_EVIDENCE","missing":missing}
    return {"status":"GROUNDED"}

def assess_all(claims,evidence):
    idx={e["evidence_id"]:e for e in evidence}
    return [{"claim_id":c["claim_id"],**assess_claim(c,idx)} for c in claims]
