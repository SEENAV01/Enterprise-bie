from dataclasses import dataclass
@dataclass(frozen=True)
class FadingStep:
    stage:int; support_fraction:float; learner_action:str
def fading_plan(total_steps,mastery,stages=3):
    if total_steps<1 or stages<1 or not 0<=mastery<=1: raise ValueError('inputs')
    start=max(.25,1-mastery*.6); out=[]
    for i in range(stages):
        frac=max(0,start*(1-i/max(1,stages-1))); action='study full solution' if frac>.7 else 'complete partial solution' if frac>.2 else 'solve independently'; out.append(FadingStep(i+1,round(frac,4),action))
    return tuple(out)
