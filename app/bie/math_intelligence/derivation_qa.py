from dataclasses import dataclass
@dataclass(frozen=True)
class DerivationQA:
 passed:bool; score:float; failures:tuple[str,...]
def assess(total_steps:int,valid_steps:int,chain_connected:bool,assumptions_resolved:bool)->DerivationQA:
 if total_steps<=0 or valid_steps<0 or valid_steps>total_steps:raise ValueError("invalid step counts")
 f=[]
 if valid_steps!=total_steps:f.append("invalid_steps")
 if not chain_connected:f.append("chain_break")
 if not assumptions_resolved:f.append("unresolved_assumptions")
 score=(valid_steps/total_steps)*(.8)+(.1 if chain_connected else 0)+(.1 if assumptions_resolved else 0)
 return DerivationQA(not f,round(score,6),tuple(f))
