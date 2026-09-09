def claim(claim_id,text,claim_type="FACTUAL",
          source_refs=None,concept_refs=None,units=None):
    return {"claim_id":claim_id,"text":text,"claim_type":claim_type,
            "source_refs":source_refs or [],"concept_refs":concept_refs or [],
            "units":units or []}
