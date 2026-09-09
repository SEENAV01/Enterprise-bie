from dataclasses import dataclass
@dataclass(frozen=True)
class CausalStep: cause:str; effect:str; mechanism:str; evidence_id:str
def build_chain(steps):
 if not steps:raise ValueError("steps required")
 for s in steps:
  if not all((s.cause.strip(),s.effect.strip(),s.mechanism.strip(),s.evidence_id.strip())):raise ValueError("grounded step required")
 for a,b in zip(steps,steps[1:]):
  if a.effect!=b.cause:raise ValueError("discontinuous causal chain")
 return tuple(steps)
