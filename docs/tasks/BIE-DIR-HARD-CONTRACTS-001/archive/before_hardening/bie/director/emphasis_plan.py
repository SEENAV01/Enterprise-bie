from dataclasses import dataclass
@dataclass(frozen=True)
class EmphasisDecision: concept_id:str; emphasis:float; reasons:tuple[str,...]
def plan_emphasis(concepts):
    out=[]
    for cid,importance,risk,assessment in concepts:
        if not cid.strip() or any(not 0<=x<=1 for x in (importance,risk,assessment)): raise ValueError("inputs")
        score=.45*importance+.3*risk+.25*assessment; reasons=[]
        if importance>=.7: reasons.append("core concept")
        if risk>=.5: reasons.append("misconception risk")
        if assessment>=.5: reasons.append("assessment importance")
        out.append(EmphasisDecision(cid,score,tuple(reasons)))
    return tuple(sorted(out,key=lambda x:(-x.emphasis,x.concept_id)))
