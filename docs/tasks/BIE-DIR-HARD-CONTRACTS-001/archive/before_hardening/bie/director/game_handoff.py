from dataclasses import dataclass
@dataclass(frozen=True)
class GameHandoff: lesson_id:str; objective_ids:tuple[str,...]; concept_ids:tuple[str,...]; misconception_ids:tuple[str,...]; mastery_checks:tuple[str,...]; evidence_ids:tuple[str,...]; forbidden_ungrounded_mechanics:bool=True
def build_game_handoff(lesson_id,objective_ids,concept_ids,misconception_ids,mastery_checks,evidence_ids):
    if not lesson_id.strip() or not objective_ids or not concept_ids or not mastery_checks or not evidence_ids: raise ValueError("grounded handoff")
    return GameHandoff(lesson_id,tuple(sorted(set(objective_ids))),tuple(sorted(set(concept_ids))),tuple(sorted(set(misconception_ids))),tuple(sorted(set(mastery_checks))),tuple(sorted(set(evidence_ids))),True)
