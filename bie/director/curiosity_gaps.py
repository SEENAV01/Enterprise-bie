from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class CuriosityGap: gap_id:str; question:str; reveal_after_scene:str; evidence_ids:tuple[str,...]
def create_curiosity_gap(gap_id,question,reveal_after_scene,evidence_ids):
    nonblank(gap_id,"gap id"); nonblank(question,"question"); nonblank(reveal_after_scene,"reveal scene")
    if "?" not in question: raise ValueError("question required")
    evidence_ids=ids(evidence_ids,"curiosity evidence",canonical=True)
    return CuriosityGap(gap_id,question,reveal_after_scene,tuple(sorted(set(evidence_ids))))
