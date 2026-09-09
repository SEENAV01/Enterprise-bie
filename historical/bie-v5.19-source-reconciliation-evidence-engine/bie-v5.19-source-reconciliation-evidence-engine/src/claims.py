def claim(claim_id,text,source_refs=None,concept_refs=None,
          status="UNRECONCILED"):
    return {"claim_id":claim_id,"text":text,"source_refs":source_refs or [],
            "concept_refs":concept_refs or [],"status":status}

def evidence(evidence_id,claim_id,source_id,locator,support="SUPPORTS",
             strength=None,notes=None):
    return {"evidence_id":evidence_id,"claim_id":claim_id,
            "source_id":source_id,"locator":locator,"support":support,
            "strength":strength,"notes":notes}
