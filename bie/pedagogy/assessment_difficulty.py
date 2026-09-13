from dataclasses import dataclass
@dataclass(frozen=True)
class AssessmentDifficulty:
    score:float; band:str
def estimate_assessment_difficulty(cognitive_level,novelty,steps,scaffolding):
    if cognitive_level not in range(1,7) or not 0<=novelty<=1 or steps<1 or not 0<=scaffolding<=1: raise ValueError('inputs')
    level=(cognitive_level-1)/5; step=min(1,steps/10); score=max(0,min(1,.4*level+.3*novelty+.2*step+.1*(1-scaffolding)))
    return AssessmentDifficulty(score,'EASY' if score<.35 else 'MEDIUM' if score<.7 else 'HARD')
