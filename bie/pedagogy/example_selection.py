from dataclasses import dataclass
@dataclass(frozen=True)
class ExampleCandidate:
    example_id:str; concept_ids:tuple[str,...]; evidence_ids:tuple[str,...]; difficulty:float; relevance:float; misconception_ids:tuple[str,...]=()
@dataclass(frozen=True)
class ExampleSelection:
    example_id:str; score:float; rationale:str
def select_example(candidates,target_concepts,target_difficulty=.5,target_misconceptions=()):
    if not 0<=target_difficulty<=1: raise ValueError('difficulty')
    targets=set(target_concepts); mis=set(target_misconceptions)
    if not targets: raise ValueError('targets')
    scored=[]
    for c in candidates:
        if not c.example_id.strip() or not c.evidence_ids or not 0<=c.difficulty<=1 or not 0<=c.relevance<=1: raise ValueError('candidate')
        cov=len(targets&set(c.concept_ids))/len(targets); mb=(len(mis&set(c.misconception_ids))/len(mis)) if mis else 0; fit=1-abs(c.difficulty-target_difficulty)
        scored.append((.5*cov+.25*c.relevance+.15*fit+.1*mb,c.example_id))
    if not scored: raise ValueError('candidates')
    score,eid=max(scored,key=lambda x:(x[0],x[1])); return ExampleSelection(eid,score,'coverage+relevance+difficulty-fit+misconception alignment')
