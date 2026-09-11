"""RE-TEMP-041 — Build deterministic pairwise temporal evidence conflict records."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TemporalClaim:
    claim_id:str
    subject:str
    relation:str
    object:str
_OPPOSITES={("before","after"),("after","before")}
def temporal_claim_conflicts(a:TemporalClaim,b:TemporalClaim):
    same=(a.subject,a.object)==(b.subject,b.object)
    reverse=(a.subject,a.object)==(b.object,b.subject)
    if same and (a.relation,b.relation) in _OPPOSITES:return True
    if reverse and a.relation==b.relation and a.relation in {"before","after"}:return True
    return False
def conflict_pairs(claims):
    xs=sorted(claims,key=lambda x:x.claim_id)
    return tuple((a.claim_id,b.claim_id) for i,a in enumerate(xs) for b in xs[i+1:] if temporal_claim_conflicts(a,b))
