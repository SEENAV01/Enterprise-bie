from dataclasses import dataclass
@dataclass(frozen=True)
class MathLink:
 equation_id:str; target_id:str; modality:str; semantic_relation:str; confidence:float
def link(equation_id,target_id,modality,relation,confidence):
 if modality not in {"graph","figure","table"}:raise ValueError("unsupported modality")
 if not all(str(x).strip() for x in (equation_id,target_id,relation)):raise ValueError("complete link required")
 c=float(confidence)
 if not 0<=c<=1:raise ValueError("confidence out of range")
 return MathLink(equation_id,target_id,modality,relation,c)
def targets(links,modality):return tuple(x.target_id for x in links if x.modality==modality)
