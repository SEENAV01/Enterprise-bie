from __future__ import annotations
from ..canonical import fingerprint
from ..errors import GameContractError
from .contracts import ChallengeProgress,ChallengeStatus

def new_progress(challenge_id,snapshot_id,ready=True):
    s=ChallengeStatus.READY if ready else ChallengeStatus.LOCKED
    body={'challenge_id':challenge_id,'status':s.value,'attempts':0,'hints_used':0,'last_snapshot_id':snapshot_id}
    return ChallengeProgress(challenge_id,s,0,0,snapshot_id,fingerprint(body),False).validate()

def _advance(p,status=None,attempt_delta=0,hint_delta=0,snapshot_id=None):
    ns=status or p.status;attempts=p.attempts+attempt_delta;hints=p.hints_used+hint_delta;sid=snapshot_id or p.last_snapshot_id
    body={'challenge_id':p.challenge_id,'previous':p.history_fingerprint,'status':ns.value,'attempts':attempts,'hints_used':hints,'last_snapshot_id':sid}
    return ChallengeProgress(p.challenge_id,ns,attempts,hints,sid,fingerprint(body),False).validate()

def start_challenge(p,snapshot_id):
    if p.status!=ChallengeStatus.READY:raise GameContractError('GAME_STATE_CHALLENGE_START_INVALID')
    return _advance(p,ChallengeStatus.ACTIVE,snapshot_id=snapshot_id)
def record_attempt(p,snapshot_id):
    if p.status!=ChallengeStatus.ACTIVE:raise GameContractError('GAME_STATE_CHALLENGE_ATTEMPT_INVALID')
    return _advance(p,attempt_delta=1,snapshot_id=snapshot_id)
def use_hint(p):
    if p.status!=ChallengeStatus.ACTIVE:raise GameContractError('GAME_STATE_CHALLENGE_HINT_INVALID')
    return _advance(p,hint_delta=1)
def finish_challenge(p,succeeded,snapshot_id):
    if p.status!=ChallengeStatus.ACTIVE:raise GameContractError('GAME_STATE_CHALLENGE_FINISH_INVALID')
    return _advance(p,ChallengeStatus.SUCCEEDED if succeeded else ChallengeStatus.FAILED,snapshot_id=snapshot_id)
