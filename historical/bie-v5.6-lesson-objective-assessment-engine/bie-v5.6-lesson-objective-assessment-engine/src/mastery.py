def mastery_update(previous, assessment_score, confidence=1.0):
    previous=float(previous)
    observed=max(0,min(1,float(assessment_score)))
    c=max(0,min(1,float(confidence)))
    updated=previous*(1-0.35*c)+observed*(0.35*c)
    return round(updated,3)

def mastery_status(score):
    if score>=0.85: return "MASTERED"
    if score>=0.70: return "READY"
    if score>=0.50: return "DEVELOPING"
    return "NOT_READY"
