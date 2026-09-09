def source_change_gate(change_type,confidence=1.0):
    destructive={"DELETE","UNTRUSTED_REPLACEMENT"}
    if change_type in destructive:
        return {"status":"BLOCK","reason":"HIGH_RISK_SOURCE_CHANGE"}
    if confidence<0.8:
        return {"status":"REVIEW","reason":"LOW_CHANGE_CONFIDENCE"}
    return {"status":"PROCEED","reason":"CHANGE_ACCEPTED"}

def protect_canonical(record_id,validated=True):
    return {"record_id":record_id,"protected":validated}
