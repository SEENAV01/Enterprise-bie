def evidence(evidence_id,source_ref,excerpt_ref=None,
             support_level="UNKNOWN",notes=None):
    return {"evidence_id":evidence_id,"source_ref":source_ref,
            "excerpt_ref":excerpt_ref,"support_level":support_level,
            "notes":notes}

def support_claim(claim_id,evidence_ids):
    return {"claim_id":claim_id,"evidence_ids":evidence_ids}
