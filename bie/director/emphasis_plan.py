from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class EmphasisDecision: concept_id:str; emphasis:float; reasons:tuple[str,...]
def plan_emphasis(concepts):
    out=[]; seen=set()
    for row in items(concepts,"emphasis concepts"):
        row=items(row,"emphasis row")
        if len(row)!=4: raise ValueError("concept and three scores required")
        cid,importance,risk,assessment=row
        nonblank(cid,"concept id")
        if cid in seen: raise ValueError("duplicate emphasis concept")
        seen.add(cid)
        for value in (importance,risk,assessment): finite(value,"emphasis score",high=1)
        if not cid.strip() or any(not 0<=x<=1 for x in (importance,risk,assessment)): raise ValueError("inputs")
        score=.45*importance+.3*risk+.25*assessment; reasons=[]
        if importance>=.7: reasons.append("core concept")
        if risk>=.5: reasons.append("misconception risk")
        if assessment>=.5: reasons.append("assessment importance")
        out.append(EmphasisDecision(cid,score,tuple(reasons)))
    return tuple(sorted(out,key=lambda x:(-x.emphasis,x.concept_id)))
