def confidence(score,evidence_count,
               evaluator_agreement=1.0):
    evidence_factor=min(1.0,evidence_count/5)
    value=max(0.0,min(1.0,
        score*0.7+evidence_factor*0.2+evaluator_agreement*0.1))
    return value

def confidence_band(value):
    if value>=0.9: return "HIGH"
    if value>=0.7: return "MEDIUM"
    return "LOW"
