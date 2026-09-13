from dataclasses import dataclass
@dataclass(frozen=True)
class BridgeExitReport:
    passed:bool; unmet_concepts:tuple[str,...]; scores:tuple[tuple[str,float],...]; requires_review:bool
def check_bridge_exit(required_scores,achieved_scores,minimum_attempts=None,achieved_attempts=None):
    if not required_scores: raise ValueError('required scores')
    minimum_attempts=dict(minimum_attempts or {}); achieved_attempts=dict(achieved_attempts or {}); unmet=[]; pairs=[]
    for c,req in sorted(required_scores.items()):
        if not 0<=req<=1: raise ValueError('required score')
        score=achieved_scores.get(c); need=minimum_attempts.get(c,1)
        if need<1: raise ValueError('attempts')
        if score is None or not 0<=score<=1: unmet.append(c); continue
        pairs.append((c,score))
        if score<req or achieved_attempts.get(c,0)<need: unmet.append(c)
    return BridgeExitReport(not unmet,tuple(unmet),tuple(pairs),bool(unmet))
