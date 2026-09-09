def citation_packet(claim_id,citations):
    return {"claim_id":claim_id,"citations":citations}

def citation_complete(claim,evidence_items):
    ids={e["evidence_id"] for e in evidence_items}
    missing=[x for x in claim.get("evidence_ids",[]) if x not in ids]
    return {"valid":not missing,"missing":missing}
