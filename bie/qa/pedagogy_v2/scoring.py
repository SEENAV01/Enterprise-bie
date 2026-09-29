"""Compute a criterion-score decision; never infer that a learner was assessed."""
from dataclasses import dataclass
from ..release_v2.contracts import ContractError,integer
from .models import ObjectiveRequirement

@dataclass(frozen=True,slots=True)
class ScoreDecision:
    earned_points:int
    maximum_points:int
    failed_criteria:tuple[str,...]
    threshold_met:bool
    criterion_floors_met:bool
    passed:bool
    learner_mastery_observed:bool=False

def check_mastery_scores(points:tuple[tuple[str,int],...],requirement:ObjectiveRequirement):
    if type(requirement) is not ObjectiveRequirement or type(points) is not tuple:raise ContractError('INVALID_MASTERY_SCORE_INPUT')
    wanted={c.criterion_id:c for c in requirement.criteria};actual={}
    for p in points:
        if type(p) is not tuple or len(p)!=2:raise ContractError('INVALID_CRITERION_SCORE')
        k,v=p
        if type(k) is not str or k not in wanted or k in actual:raise ContractError('INVALID_CRITERION_SCORE_ID')
        integer(v,'criterion score',0,wanted[k].max_points);actual[k]=v
    if set(actual)!=set(wanted):raise ContractError('CRITERION_SCORES_INCOMPLETE')
    maximum=sum(c.max_points for c in wanted.values());earned=sum(actual.values())
    failed=tuple(sorted(k for k,c in wanted.items() if actual[k]<c.minimum_points))
    threshold=earned*1000000>=maximum*requirement.mastery_threshold_ppm
    return ScoreDecision(earned,maximum,failed,threshold,not failed,threshold and not failed)
