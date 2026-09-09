def evaluate_response(question,answer):
    expected=question.get("correct_answer")
    if expected is None:
        return {"status":"REVIEW_REQUIRED","score":None,"feedback":"Manual/rubric evaluation required."}
    correct=answer==expected
    return {"status":"CORRECT" if correct else "INCORRECT",
            "score":1.0 if correct else 0.0,
            "feedback":"Correct." if correct else "Try again."}

def evaluate_with_rubric(rubric,answer):
    if not rubric:
        return {"status":"REVIEW_REQUIRED","score":None}
    return {"status":"RUBRIC_REVIEW","score":None,"rubric":rubric,"answer":answer}
