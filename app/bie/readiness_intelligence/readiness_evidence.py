from dataclasses import dataclass
@dataclass(frozen=True)
class ReadinessEvidence:
 source:str; score:float; reliability:float
@dataclass(frozen=True)
class ReadinessDecision:
 ready:bool; confidence:float; weighted_score:float; evidence_count:int; reason:str
def decide_readiness(evidence:list[ReadinessEvidence], threshold:float=.75, min_evidence:int=1)->ReadinessDecision:
 if not 0<=threshold<=1 or min_evidence<1: raise ValueError("invalid policy")
 if any(not(0<=e.score<=1 and 0<=e.reliability<=1) for e in evidence): raise ValueError("evidence values out of range")
 weight=sum(e.reliability for e in evidence)
 score=(sum(e.score*e.reliability for e in evidence)/weight) if weight else 0.0
 confidence=min(1.0,(weight/max(1,len(evidence)))*min(1.0,len(evidence)/min_evidence)) if evidence else 0.0
 enough=len(evidence)>=min_evidence and weight>0
 ready=enough and score>=threshold
 reason="ready" if ready else ("insufficient_evidence" if not enough else "below_threshold")
 return ReadinessDecision(ready,round(confidence,6),round(score,6),len(evidence),reason)
