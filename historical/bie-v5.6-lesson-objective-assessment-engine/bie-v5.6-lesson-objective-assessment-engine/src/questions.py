QUESTION_TYPES=[
"CONCEPTUAL","NUMERICAL","APPLICATION","MISCONCEPTION",
"TRANSFER","EXPLANATION","MULTI_STEP"
]

def question(question_id, objective_id, qtype, prompt, answer,
             distractors=None, difficulty="MEDIUM"):
    if qtype not in QUESTION_TYPES: raise ValueError("UNKNOWN_QUESTION_TYPE")
    return {
      "question_id":question_id,
      "objective_id":objective_id,
      "type":qtype,
      "prompt":prompt,
      "answer":answer,
      "distractors":distractors or [],
      "difficulty":difficulty
    }
