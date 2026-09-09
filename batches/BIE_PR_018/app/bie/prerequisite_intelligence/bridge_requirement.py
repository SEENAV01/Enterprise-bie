from dataclasses import dataclass
@dataclass(frozen=True)
class BridgeRequirement:
 required:bool; missing:tuple[str,...]; risk:float
def bridge_requirement(required_prereqs:set[str], available:set[str], strengths:dict[str,float]|None=None, risk_threshold:float=.4)->BridgeRequirement:
 strengths=strengths or {}
 missing=tuple(sorted(required_prereqs-available))
 risk=max((strengths.get(p,.5) for p in missing),default=0.0)
 return BridgeRequirement(bool(missing and risk>=risk_threshold),missing,round(risk,6))
