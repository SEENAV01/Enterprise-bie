def quality_gate(score,threshold):
    return {"valid":score>=threshold,
            "score":score,"threshold":threshold,
            "reason":"PASS" if score>=threshold else "QUALITY_THRESHOLD"}

def promotion_gate(evaluation,regression_result=None):
    if not evaluation.get("passed",False):
        return {"allowed":False,"reason":"EVALUATION_FAILED"}
    if regression_result and regression_result.get("regression"):
        return {"allowed":False,"reason":"REGRESSION_DETECTED"}
    return {"allowed":True,"reason":"QUALITY_APPROVED"}
