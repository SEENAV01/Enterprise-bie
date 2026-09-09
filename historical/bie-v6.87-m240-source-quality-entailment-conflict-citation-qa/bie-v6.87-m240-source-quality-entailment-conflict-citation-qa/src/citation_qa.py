def citation_completeness(claims,citation_map):
    mapped={x.get("claim_id") for x in citation_map if x.get("evidence")}
    cited=sum(c.get("claim_id") in mapped for c in claims)
    return {"claims":len(claims),"cited_claims":cited,
            "completeness":cited/len(claims) if claims else 1.0}

def citation_gate(completeness,quality_checks,entailment_checks,conflicts):
    return {"valid":completeness["completeness"]>=1 and
            all(x["passed"] for x in quality_checks+entailment_checks) and not conflicts,
            "completeness":completeness,"conflicts":conflicts}
