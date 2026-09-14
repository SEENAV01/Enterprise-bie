from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class DerivationNarrationStep: index:int; expression:str; narration:str; evidence_ids:tuple[str,...]
def narrate_derivation(steps):
    out=[]
    for i,row in enumerate(items(steps,"derivation steps"),1):
        row=items(row,"derivation step")
        if len(row)!=3: raise ValueError("expression, reason and evidence required")
        expr,why,ev=row; nonblank(expr,"expression"); nonblank(why,"reason")
        ev=ids(ev,"derivation evidence",canonical=True)
        if not expr.strip() or not why.strip() or not ev: raise ValueError("grounding")
        out.append(DerivationNarrationStep(i,expr,f"Step {i}: {why}. This gives {expr}.",tuple(sorted(set(ev)))))
    if len(out)<2: raise ValueError("multi step")
    return tuple(out)
