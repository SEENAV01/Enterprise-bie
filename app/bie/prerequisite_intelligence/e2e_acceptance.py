from dataclasses import dataclass
@dataclass(frozen=True)
class Gate:
 name:str; passed:bool; evidence:str
@dataclass(frozen=True)
class Acceptance:
 accepted:bool; blockers:tuple[str,...]
REQUIRED=("source_grounding","graph_acyclic","necessity","bridge_scope","confidence_calibration","realbook_multidomain")
def assess(gates:list[Gate])->Acceptance:
 by={g.name:g for g in gates}
 blockers=[]
 for name in REQUIRED:
  g=by.get(name)
  if not g or not g.passed or not g.evidence.strip():blockers.append(name)
 return Acceptance(not blockers,tuple(blockers))
