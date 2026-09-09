def feedback(item_id,correct,score,explanation,misconception=None):
    return {"item_id":item_id,"correct":correct,"score":score,
            "explanation":explanation,"misconception":misconception}

def feedback_level(score):
    return "MASTERED" if score>=0.85 else ("DEVELOPING" if score>=0.60 else "NEEDS_REMEDIATION")
