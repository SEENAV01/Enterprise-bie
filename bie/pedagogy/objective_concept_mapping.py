from dataclasses import dataclass
@dataclass(frozen=True)
class ObjectiveConceptLink: objective_id:str; concept_id:str; role:str; evidence_ids:tuple[str,...]
def validate_link(x):
 if x.role not in {"PRIMARY","SUPPORTING","PREREQUISITE"} or not x.evidence_ids: raise ValueError("invalid mapping")
 return x
