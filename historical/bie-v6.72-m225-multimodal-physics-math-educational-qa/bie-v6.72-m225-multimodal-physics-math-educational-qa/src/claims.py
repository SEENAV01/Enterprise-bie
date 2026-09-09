def claim(claim_id,text,claim_type="FACT",source=None):
    return {"claim_id":claim_id,"text":text,"claim_type":claim_type,"source":source}
def validate_claim(c):
    return bool(c.get("claim_id") and c.get("text") and c.get("claim_type"))
