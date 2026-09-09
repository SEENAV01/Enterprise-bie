from dataclasses import dataclass
@dataclass(frozen=True)
class Assessment: kind:str; objective_fit:float; diagnostic_power:float; transfer_value:float
def decide(items):
 if not items:raise ValueError("assessment candidates required")
 for x in items:
  if any(v<0 or v>1 for v in (x.objective_fit,x.diagnostic_power,x.transfer_value)):raise ValueError("normalized scores")
 return max(items,key=lambda x:(.5*x.objective_fit+.3*x.diagnostic_power+.2*x.transfer_value,x.kind))
