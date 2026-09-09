from dataclasses import dataclass
@dataclass(frozen=True)
class EvidenceVote:
 source:str; supports:bool; reliability:float
@dataclass(frozen=True)
class Arbitration:
 accepted:bool|None; support:float; oppose:float; status:str
def arbitrate(votes:list[EvidenceVote],margin:float=.15)->Arbitration:
 if any(not 0<=v.reliability<=1 for v in votes): raise ValueError("reliability out of range")
 support=sum(v.reliability for v in votes if v.supports); oppose=sum(v.reliability for v in votes if not v.supports)
 total=support+oppose
 s=support/total if total else 0; o=oppose/total if total else 0
 if not total:return Arbitration(None,0,0,"insufficient_evidence")
 if abs(s-o)<margin:return Arbitration(None,round(s,6),round(o,6),"unresolved_conflict")
 return Arbitration(s>o,round(s,6),round(o,6),"accepted" if s>o else "rejected")
