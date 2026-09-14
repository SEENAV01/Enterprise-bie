from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class DemoNarrationStep: phase:str; narration:str; evidence_ids:tuple[str,...]
def narrate_demonstration(setup,action,observation,interpretation,evidence_ids):
    for value in (setup,action,observation,interpretation): nonblank(value,"demonstration narration")
    evidence_ids=ids(evidence_ids,"demonstration evidence",canonical=True)
    ev=tuple(sorted(set(evidence_ids)))
    return (DemoNarrationStep("SETUP",setup,ev),DemoNarrationStep("ACTION",action,ev),DemoNarrationStep("OBSERVE",observation,ev),DemoNarrationStep("INTERPRET",interpretation,ev))
