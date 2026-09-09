
from dataclasses import dataclass,field
from typing import Dict,List
class AcceptanceError(ValueError): pass
@dataclass(frozen=True)
class Criterion:
 id:str; description:str; required_evidence_types:tuple
@dataclass(frozen=True)
class Evidence:
 ref:str; evidence_type:str; passed:bool; artifact_hash:str
class AcceptanceBinder:
 def __init__(self,criteria:List[Criterion]): self.criteria=criteria; self.bound:Dict[str,List[Evidence]]={c.id:[] for c in criteria}
 def bind(self,criterion_id,evidence:Evidence):
  if criterion_id not in self.bound: raise AcceptanceError("unknown criterion")
  if not evidence.ref or not evidence.artifact_hash: raise AcceptanceError("immutable evidence reference/hash required")
  self.bound[criterion_id].append(evidence)
 def evaluate(self):
  failures={}
  for c in self.criteria:
   ev=self.bound[c.id]; passed_types={e.evidence_type for e in ev if e.passed}
   missing=set(c.required_evidence_types)-passed_types
   if missing: failures[c.id]=sorted(missing)
  return {"accepted":not failures,"failures":failures}
