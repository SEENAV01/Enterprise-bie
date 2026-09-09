def compare_claims(a:dict,b:dict)->dict:
    # Conservative gate: semantic contradiction should be decided by a model,
    # but the production contract records the result explicitly.
    return {
      "claim_a":a.get("claim_id"),
      "claim_b":b.get("claim_id"),
      "relation":"REQUIRES_MODEL_JUDGMENT",
      "action":"REVIEW"
    }

def ambiguity_record(text:str,reason:str)->dict:
    return {"text":text,"reason":reason,"status":"REVIEW"}
