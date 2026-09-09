def score_response(question,response):
    correct=response==question.get("answer")
    return {"question_id":question["question_id"],"concept_id":question["concept_id"],
            "correct":correct,"score":1.0 if correct else 0.0}

def aggregate_mastery(results):
    by={}
    for r in results: by.setdefault(r["concept_id"],[]).append(r["score"])
    return {c:round(sum(v)/len(v),3) for c,v in by.items()}
