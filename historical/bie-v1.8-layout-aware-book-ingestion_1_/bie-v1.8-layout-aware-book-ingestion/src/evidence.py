def evidence_span(block):
    return {
        "evidence_id":block["block_id"],
        "page":block["page"],
        "block_type":block["block_type"],
        "text":block.get("text",""),
        "asset_ref":block.get("asset_ref"),
        "bbox":block.get("bbox")
    }

def claim_evidence(claim, refs, evidence_index):
    return {
        "claim":claim,
        "evidence":[evidence_index[r] for r in refs if r in evidence_index],
        "status":"GROUNDED" if all(r in evidence_index for r in refs) else "REVIEW"
    }
