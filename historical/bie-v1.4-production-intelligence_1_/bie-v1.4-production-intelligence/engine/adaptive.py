from dataclasses import dataclass

@dataclass
class LearnerState:
    mastery: dict[str,float]

def next_action(unit_id:str, score:float)->str:
    if score >= .85:
        return "advance"
    if score >= .60:
        return "remediate_with_visual"
    return "reteach_prerequisite_then_retry"

def choose_path(current_unit:str, score:float, prereq:list[str])->dict:
    return {
        "unit":current_unit,
        "action":next_action(current_unit,score),
        "prerequisites":prereq if score < .60 else []
    }
