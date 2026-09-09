def feedback_for(result,question):
    if result["correct"]:
        return {"type":"REINFORCE","message":"Correct. Reinforce the key idea.",
                "next_action":"PROGRESS"}
    return {"type":"RETEACH","message":question.get("rationale","Review the concept."),
            "next_action":"REVIEW"}

def feedback_batch(results,questions):
    qm={q["question_id"]:q for q in questions}
    return [feedback_for(r,qm[r["question_id"]]) for r in results if r["question_id"] in qm]
