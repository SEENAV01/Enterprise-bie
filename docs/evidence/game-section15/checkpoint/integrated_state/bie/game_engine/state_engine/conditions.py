from __future__ import annotations
from ..document import ChallengeContract,GameLevelContract
from ..canonical import fingerprint
from ..errors import GameContractError
from .contracts import ConditionEvaluation
from .expression_runtime import evaluate_typed

def evaluate_conditions(level:GameLevelContract,challenge:ChallengeContract,snapshot):
    state=snapshot.as_dict();types=level.state.type_map();success=evaluate_typed(challenge.success_condition,state,types)
    if type(success) is not bool:raise GameContractError('GAME_STATE_SUCCESS_NOT_BOOL')
    matched=[]
    for i,e in enumerate(challenge.failure_conditions):
        v=evaluate_typed(e,state,types)
        if type(v) is not bool:raise GameContractError('GAME_STATE_FAILURE_NOT_BOOL')
        if v:matched.append(i)
    failed=bool(matched)
    if success and failed:raise GameContractError('GAME_STATE_SUCCESS_FAILURE_CONFLICT')
    r=ConditionEvaluation(challenge.challenge_id,success,failed,tuple(matched),fingerprint(snapshot),False);return r.validate()

def evaluate_success(level,challenge,snapshot):return evaluate_conditions(level,challenge,snapshot).success
def evaluate_failure(level,challenge,snapshot):return evaluate_conditions(level,challenge,snapshot).failed
