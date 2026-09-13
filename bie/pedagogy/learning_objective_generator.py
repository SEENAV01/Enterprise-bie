from dataclasses import dataclass
from bie.pedagogy.pedagogy_provenance import _normalize_ids
@dataclass(frozen=True)
class LearningObjective: objective_id:str; concept_id:str; statement:str; evidence_ids:tuple[str,...]
def generate_objective(concept_id,label,evidence_ids):
 evidence_ids=_normalize_ids(evidence_ids,"objective evidence")
 if not concept_id.strip() or not label.strip() or not evidence_ids: raise ValueError("grounded concept required")
 return LearningObjective("obj:"+concept_id,concept_id,f"Explain and apply {label}.",tuple(sorted(set(evidence_ids))))
