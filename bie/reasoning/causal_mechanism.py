from dataclasses import dataclass
@dataclass(frozen=True)
class Mechanism: cause:str; mediator:str; effect:str; evidence_ids:tuple[str,...]; confidence:float
def validate(m):
 if not all((m.cause.strip(),m.mediator.strip(),m.effect.strip())) or not m.evidence_ids:raise ValueError("grounded mechanism required")
 if len({m.cause,m.mediator,m.effect})<3:raise ValueError("distinct causal roles required")
 if not 0<=m.confidence<=1:raise ValueError("confidence")
 return True
