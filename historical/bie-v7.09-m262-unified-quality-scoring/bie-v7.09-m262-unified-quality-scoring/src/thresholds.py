def evaluate_threshold(score, threshold=90.0, hard_failures=None):
    hard_failures=hard_failures or []
    if hard_failures:
        return {"status":"BLOCKED","release":False,"reasons":hard_failures}
    if score>=threshold:
        return {"status":"PASS","release":True,"reasons":[]}
    return {"status":"REVIEW","release":False,"reasons":["SCORE_BELOW_THRESHOLD"]}

def level_thresholds(scene=90.0, lesson=92.0, course=94.0):
    return {"scene":scene,"lesson":lesson,"course":course}
