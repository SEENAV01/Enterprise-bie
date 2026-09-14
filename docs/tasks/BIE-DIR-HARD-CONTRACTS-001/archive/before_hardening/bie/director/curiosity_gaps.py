from dataclasses import dataclass
@dataclass(frozen=True)
class CuriosityGap: gap_id:str; question:str; reveal_after_scene:str; evidence_ids:tuple[str,...]
def create_curiosity_gap(gap_id,question,reveal_after_scene,evidence_ids):
    if not gap_id.strip() or "?" not in question or not reveal_after_scene.strip() or not evidence_ids: raise ValueError("grounded question")
    return CuriosityGap(gap_id,question,reveal_after_scene,tuple(sorted(set(evidence_ids))))
