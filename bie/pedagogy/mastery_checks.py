from dataclasses import dataclass
@dataclass(frozen=True)
class MasteryCheckResult:
    objective_id:str; score:float; transfer_passed:bool; attempts:int; mastered:bool
def evaluate_mastery(objective_id,score,transfer_passed,attempts,threshold=.8,min_attempts=2,transfer_required=True):
    if not objective_id.strip() or not 0<=score<=1 or attempts<0 or not 0<=threshold<=1 or min_attempts<1: raise ValueError('inputs')
    mastered=score>=threshold and attempts>=min_attempts and (transfer_passed or not transfer_required)
    return MasteryCheckResult(objective_id,score,bool(transfer_passed),attempts,mastered)
