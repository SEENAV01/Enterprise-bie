"""Original BIE-DIR-SCRIPT-010; reject empty or malformed learning-model IDs."""
from dataclasses import dataclass
from .contract_validation import nonblank,ids


@dataclass(frozen=True)
class GameHandoff:
    lesson_id:str
    objective_ids:tuple[str,...]
    concept_ids:tuple[str,...]
    misconception_ids:tuple[str,...]
    mastery_checks:tuple[str,...]
    evidence_ids:tuple[str,...]
    forbidden_ungrounded_mechanics:bool=True


def build_game_handoff(lesson_id,objective_ids,concept_ids,misconception_ids,mastery_checks,evidence_ids):
    nonblank(lesson_id,'lesson id')
    return GameHandoff(lesson_id,ids(objective_ids,'game objectives',canonical=True),ids(concept_ids,'game concepts',canonical=True),
        ids(misconception_ids,'game misconceptions',required=False,canonical=True),ids(mastery_checks,'game mastery checks',canonical=True),
        ids(evidence_ids,'game evidence',canonical=True),True)


def validate_game_handoff(value):
    if not isinstance(value,GameHandoff): raise ValueError('expected GameHandoff')
    rebuilt=build_game_handoff(value.lesson_id,value.objective_ids,value.concept_ids,value.misconception_ids,value.mastery_checks,value.evidence_ids)
    if value!=rebuilt or value.forbidden_ungrounded_mechanics is not True:
        raise ValueError('noncanonical or weakened game handoff')
    return value
