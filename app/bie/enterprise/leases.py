from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Callable, List
import time

class LeaseError(ValueError): pass

@dataclass(frozen=True)
class LeaseKey:
    run_id:str
    stage_id:str
    attempt:int
    def validate(self):
        if not self.run_id or not self.stage_id or self.attempt<1:
            raise LeaseError("invalid lease key")

@dataclass(frozen=True)
class LeaseToken:
    key:LeaseKey
    worker_id:str
    fencing_token:int
    acquired_at:float
    expires_at:float

    def validate(self):
        self.key.validate()
        if not self.worker_id: raise LeaseError("worker_id required")
        if self.fencing_token<1: raise LeaseError("invalid fencing token")
        if self.expires_at<=self.acquired_at: raise LeaseError("invalid lease interval")

@dataclass(frozen=True)
class RecoveryEvidence:
    key:LeaseKey
    previous_worker_id:str
    previous_fencing_token:int
    detected_at:float
    reason:str="lease_expired"

class LeaseManager:
    def __init__(self,clock:Optional[Callable[[],float]]=None):
        self.clock=clock or time.time
        self._active:Dict[LeaseKey,LeaseToken]={}
        self._generation:Dict[LeaseKey,int]={}
        self._recovery:List[RecoveryEvidence]=[]

    def _now(self)->float:
        return float(self.clock())

    def _expired(self,t:LeaseToken)->bool:
        return self._now() >= t.expires_at

    def acquire(self,key:LeaseKey,worker_id:str,ttl_seconds:float)->LeaseToken:
        key.validate()
        if not worker_id: raise LeaseError("worker_id required")
        if ttl_seconds<=0: raise LeaseError("ttl must be >0")

        existing=self._active.get(key)
        if existing is not None and not self._expired(existing):
            raise LeaseError("stage attempt already leased")

        if existing is not None and self._expired(existing):
            self._recovery.append(RecoveryEvidence(
                key,existing.worker_id,existing.fencing_token,self._now()
            ))

        generation=self._generation.get(key,0)+1
        self._generation[key]=generation
        now=self._now()
        token=LeaseToken(key,worker_id,generation,now,now+ttl_seconds)
        self._active[key]=token
        return token

    def renew(self,token:LeaseToken,ttl_seconds:float)->LeaseToken:
        if ttl_seconds<=0: raise LeaseError("ttl must be >0")
        self.assert_current(token,require_unexpired=True)
        now=self._now()
        renewed=LeaseToken(token.key,token.worker_id,token.fencing_token,token.acquired_at,now+ttl_seconds)
        self._active[token.key]=renewed
        return renewed

    def release(self,token:LeaseToken)->None:
        self.assert_current(token,require_unexpired=False)
        self._active.pop(token.key,None)

    def assert_current(self,token:LeaseToken,require_unexpired:bool=True)->None:
        token.validate()
        current=self._active.get(token.key)
        if current is None: raise LeaseError("no active lease")
        if current.worker_id!=token.worker_id or current.fencing_token!=token.fencing_token:
            raise LeaseError("stale or foreign fencing token")
        if require_unexpired and self._expired(current):
            raise LeaseError("lease expired")

    def commit_guard(self,token:LeaseToken)->None:
        self.assert_current(token,require_unexpired=True)

    def mark_expired_recoverable(self,key:LeaseKey)->RecoveryEvidence:
        key.validate()
        current=self._active.get(key)
        if current is None: raise LeaseError("no lease to recover")
        if not self._expired(current): raise LeaseError("lease not expired")
        ev=RecoveryEvidence(key,current.worker_id,current.fencing_token,self._now())
        self._recovery.append(ev)
        self._active.pop(key,None)
        return ev

    def active_lease(self,key:LeaseKey)->Optional[LeaseToken]:
        t=self._active.get(key)
        if t is None:return None
        if self._expired(t):return None
        return t

    def recovery_evidence(self)->List[RecoveryEvidence]:
        return list(self._recovery)

class WorkerOwnershipGuard:
    def __init__(self,leases:LeaseManager):
        self.leases=leases

    def authorize_state_write(self,token:LeaseToken,run_id:str,stage_id:str,attempt:int)->None:
        if token.key != LeaseKey(run_id,stage_id,attempt):
            raise LeaseError("lease scope mismatch")
        self.leases.commit_guard(token)

    def authorize_artifact_write(self,token:LeaseToken,run_id:str,stage_id:str,attempt:int)->None:
        self.authorize_state_write(token,run_id,stage_id,attempt)
