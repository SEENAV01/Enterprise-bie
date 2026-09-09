from dataclasses import dataclass
@dataclass(frozen=True)
class Remediation:
 misconception:str; strategy:str; steps:tuple[str,...]
def remediation_for(misconception:str, kind:str, severity:str)->Remediation:
 strategies={
  "confusion":("contrast_cases",("state competing ideas","show side-by-side cases","ask learner to discriminate")),
  "overgeneralization":("counterexample",("state rule","show boundary-breaking counterexample","restate valid scope")),
  "causal":("mechanism_rebuild",("surface prediction","trace mechanism","test revised prediction")),
  "procedural":("worked_error_analysis",("show erroneous step","locate first invalid step","redo with justification")),
 }
 strategy,steps=strategies.get(kind,("diagnose_and_reteach",("elicit learner model","provide corrective evidence","verify transfer")))
 if severity in {"high","critical"}: steps=steps+("schedule delayed retrieval check",)
 return Remediation(misconception,strategy,steps)
