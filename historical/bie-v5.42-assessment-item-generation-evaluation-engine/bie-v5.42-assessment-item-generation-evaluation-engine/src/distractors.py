def distractor(distractor_id,text,misconception_ref=None,
               rationale=None):
    return {"distractor_id":distractor_id,"text":text,
            "misconception_ref":misconception_ref,
            "rationale":rationale}

def validate_distractors(choices,correct_answer):
    errors=[]
    texts=[c.get("text") for c in choices]
    if len(texts)!=len(set(texts)): errors.append("DUPLICATE_CHOICE")
    if not any(c.get("text")==correct_answer for c in choices):
        errors.append("CORRECT_ANSWER_NOT_IN_CHOICES")
    return sorted(set(errors))
