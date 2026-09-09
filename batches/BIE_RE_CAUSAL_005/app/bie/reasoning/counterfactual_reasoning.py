from dataclasses import dataclass
@dataclass(frozen=True)
class Counterfactual: intervention:str; baseline:str; predicted:str; changed:bool; evidence_ids:tuple[str,...]
def assess(intervention,baseline,predicted,evidence_ids):
 if not all(str(x).strip() for x in (intervention,baseline,predicted)) or not evidence_ids:raise ValueError("grounded counterfactual required")
 return Counterfactual(intervention,baseline,predicted,baseline!=predicted,tuple(evidence_ids))
