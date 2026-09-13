from dataclasses import dataclass
@dataclass(frozen=True)
class Counterexample:
    counterexample_id:str; misconception_ids:tuple[str,...]; concept_ids:tuple[str,...]; evidence_ids:tuple[str,...]; clarity:float
def select_counterexample(candidates,misconception_id,concept_id):
    if not misconception_id.strip() or not concept_id.strip(): raise ValueError('targets')
    valid=[]
    for c in candidates:
        if not c.evidence_ids or not 0<=c.clarity<=1: raise ValueError('candidate')
        if misconception_id in c.misconception_ids and concept_id in c.concept_ids: valid.append(c)
    if not valid: raise ValueError('no grounded counterexample')
    return max(valid,key=lambda c:(c.clarity,c.counterexample_id))
