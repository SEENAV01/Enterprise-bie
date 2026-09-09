def uncertainty_record(level,reason,alternatives=None):
    return {"level":level,"reason":reason,"alternatives":alternatives or []}

def decision_status(confidence,threshold=0.75):
    if confidence is None: return "REVIEW_REQUIRED"
    if confidence>=threshold: return "ACCEPTED"
    if confidence>=0.5: return "TENTATIVE"
    return "REVIEW_REQUIRED"
