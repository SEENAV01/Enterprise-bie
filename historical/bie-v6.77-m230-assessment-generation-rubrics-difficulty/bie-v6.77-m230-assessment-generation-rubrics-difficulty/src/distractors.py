def distractors(correct,misconceptions,minimum=3):
    result=[m for m in misconceptions if m!=correct]
    while len(result)<minimum:
        result.append(f"plausible_alternative_{len(result)+1}")
    return result[:minimum]

def validate_distractors(correct,choices):
    wrong=[c for c in choices if c!=correct]
    return {"passed":bool(wrong) and correct in choices,
            "unique":len(set(choices))==len(choices),
            "count":len(choices)}
