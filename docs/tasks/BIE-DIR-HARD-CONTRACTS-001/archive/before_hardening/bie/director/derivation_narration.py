from dataclasses import dataclass
@dataclass(frozen=True)
class DerivationNarrationStep: index:int; expression:str; narration:str; evidence_ids:tuple[str,...]
def narrate_derivation(steps):
    out=[]
    for i,(expr,why,ev) in enumerate(steps,1):
        if not expr.strip() or not why.strip() or not ev: raise ValueError("grounding")
        out.append(DerivationNarrationStep(i,expr,f"Step {i}: {why}. This gives {expr}.",tuple(sorted(set(ev)))))
    if len(out)<2: raise ValueError("multi step")
    return tuple(out)
