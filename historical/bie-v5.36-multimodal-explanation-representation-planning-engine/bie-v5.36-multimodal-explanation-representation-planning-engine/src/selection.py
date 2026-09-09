def score_representation(rep,signals):
    score=rep.get("priority",1.0)
    for k,v in signals.items():
        if k in rep.get("strengths",[]):
            score+=v
    return score

def rank_representations(representations,signals=None):
    signals=signals or {}
    return sorted(representations,
                  key=lambda r:score_representation(r,signals),
                  reverse=True)
