def score_action(action,signals=None,weights=None):
    signals=signals or {}
    weights=weights or {}
    total=0.0
    for key,value in signals.items():
        if isinstance(value,(int,float)):
            total += value * weights.get(key,1.0)
    return total

def rank_actions(actions,scores):
    return sorted(actions,key=lambda a:scores.get(a["action_id"],0),
                  reverse=True)
