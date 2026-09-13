from dataclasses import dataclass
@dataclass(frozen=True)
class MasteryCriterion: score:float=.8; attempts:int=2; transfer_required:bool=True
def mastery_met(c,score,attempts,transfer):
 return score>=c.score and attempts>=c.attempts and (transfer or not c.transfer_required)
