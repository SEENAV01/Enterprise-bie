from dataclasses import dataclass
@dataclass(frozen=True)
class ExampleDifficulty:
    score:float; band:str; factors:tuple[tuple[str,float],...]
def estimate_example_difficulty(step_count,abstraction,novelty,symbolic_load,prerequisite_gap):
    if step_count<1 or any(not 0<=x<=1 for x in (abstraction,novelty,symbolic_load,prerequisite_gap)): raise ValueError('inputs')
    sf=min(1,step_count/10); score=.25*sf+.2*abstraction+.2*novelty+.2*symbolic_load+.15*prerequisite_gap
    band='EASY' if score<.35 else 'MEDIUM' if score<.7 else 'HARD'
    return ExampleDifficulty(score,band,(('steps',sf),('abstraction',abstraction),('novelty',novelty),('symbolic_load',symbolic_load),('prerequisite_gap',prerequisite_gap)))
