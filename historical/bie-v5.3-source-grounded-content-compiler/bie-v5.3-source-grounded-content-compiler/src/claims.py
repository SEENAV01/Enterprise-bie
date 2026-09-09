TYPES=["SOURCE_FACT","DERIVED","INFERRED","ENRICHMENT","EXAMPLE","INSTRUCTIONAL_REPHRASE"]

def claim(claim_id,text,claim_type="SOURCE_FACT",required=True):
    if claim_type not in TYPES: raise ValueError("UNKNOWN_CLAIM_TYPE")
    return {
      "claim_id":claim_id,"text":text,"claim_type":claim_type,
      "required":required,"evidence_ids":[],"reasoning_notes":[]
    }

def attach_evidence(c,evidence_ids):
    c["evidence_ids"]=list(dict.fromkeys(evidence_ids))
    return c
