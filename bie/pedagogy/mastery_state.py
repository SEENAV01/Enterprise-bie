from dataclasses import dataclass
@dataclass(frozen=True)
class MasteryState:
    concept_id:str; prior:float; evidence_score:float; updated:float; evidence_id:str
def update_mastery(concept_id,prior,evidence_score,evidence_id,learning_rate=.35):
    if not concept_id.strip() or not evidence_id.strip() or not 0<=prior<=1 or not 0<=evidence_score<=1 or not 0<learning_rate<=1: raise ValueError('inputs')
    return MasteryState(concept_id,prior,evidence_score,prior+learning_rate*(evidence_score-prior),evidence_id)
