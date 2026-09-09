def entailment(claim,evidence,mode="semantic"):
    claim_terms=set(claim.lower().split())
    evidence_terms=set(evidence.lower().split())
    overlap=len(claim_terms & evidence_terms)/len(claim_terms) if claim_terms else 1.0
    return {"claim_id":claim.get("claim_id"),"evidence_id":evidence.get("evidence_id"),
            "mode":mode,"score":round(overlap,3),"entailed":overlap>=0.5}

def validate_entailment(result,threshold=0.5):
    return {"passed":result["score"]>=threshold,"score":result["score"],"threshold":threshold}
