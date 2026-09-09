def mastery_update(state,evidence,threshold=0.8):
    score=evidence.get("score")
    if score is None:
        return {**state,"status":"REVIEW_REQUIRED"}
    status="MASTERED" if score>=threshold else "NOT_MASTERED"
    return {**state,"score":score,"status":status,
            "attempts":state.get("attempts",0)+1}

def mastery_summary(states):
    total=len(states)
    mastered=sum(x.get("status")=="MASTERED" for x in states)
    return {"total":total,"mastered":mastered,
            "mastery_rate":mastered/total if total else 0}
