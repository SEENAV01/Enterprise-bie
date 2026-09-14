from dataclasses import dataclass
@dataclass(frozen=True)
class DemoNarrationStep: phase:str; narration:str; evidence_ids:tuple[str,...]
def narrate_demonstration(setup,action,observation,interpretation,evidence_ids):
    if not all(x.strip() for x in (setup,action,observation,interpretation)) or not evidence_ids: raise ValueError("grounding")
    ev=tuple(sorted(set(evidence_ids)))
    return (DemoNarrationStep("SETUP",setup,ev),DemoNarrationStep("ACTION",action,ev),DemoNarrationStep("OBSERVE",observation,ev),DemoNarrationStep("INTERPRET",interpretation,ev))
