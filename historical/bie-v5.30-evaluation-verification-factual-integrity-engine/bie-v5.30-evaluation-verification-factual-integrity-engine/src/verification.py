def verify_claim(claim,evidence_items):
    ids={e.get("evidence_id") for e in evidence_items}
    refs=set(claim.get("source_refs",[]))
    supported=any(e.get("evidence_id") in ids and
                  e.get("source_ref") in refs and
                  e.get("support_level")=="SUPPORTED"
                  for e in evidence_items)
    return {"claim_id":claim["claim_id"],
            "status":"SUPPORTED" if supported else "REVIEW_REQUIRED"}

def verification_gate(results):
    blocked=[r for r in results if r.get("status")!="SUPPORTED"]
    return {"passed":not blocked,"blocked_claims":
            [r["claim_id"] for r in blocked]}
