def assessment_blueprint(objective_ids, questions,
                         required_per_objective=2):
    counts={x:0 for x in objective_ids}
    for q in questions:
        if q["objective_id"] in counts:
            counts[q["objective_id"]]+=1
    gaps=[x for x,n in counts.items() if n<required_per_objective]
    return {
      "objective_ids":objective_ids,
      "question_counts":counts,
      "coverage_complete":not gaps,
      "coverage_gaps":gaps
    }

def score_attempt(questions, responses):
    correct=0; total=len(questions); details=[]
    for q in questions:
        ok=responses.get(q["question_id"])==q["answer"]
        correct+=int(ok)
        details.append({"question_id":q["question_id"],"correct":ok})
    return {
      "score":correct/total if total else 0,
      "correct":correct,"total":total,"details":details
    }
