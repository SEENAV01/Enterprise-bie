from dataclasses import dataclass
@dataclass(frozen=True)
class Evidence:
 evidence_id:str; claim:str; support:float; source:str
@dataclass(frozen=True)
class Aggregate:
 claim:str; score:float; evidence_ids:tuple[str,...]
def aggregate(claim:str,evidence:list[Evidence])->Aggregate:
 xs=[e for e in evidence if e.claim==claim]
 if not xs:raise ValueError("evidence required")
 if any(not 0<=e.support<=1 for e in xs):raise ValueError("support out of range")
 # noisy-OR: multiple independent support signals accumulate conservatively.
 score=1.0
 for e in xs:score*=1-e.support
 return Aggregate(claim,1-score,tuple(sorted(e.evidence_id for e in xs)))
