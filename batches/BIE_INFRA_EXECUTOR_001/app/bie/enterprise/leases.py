from dataclasses import dataclass
from typing import Optional, Callable, Dict
import time

class LeaseError(ValueError): pass

@dataclass(frozen=True)
class LeaseKey:
    run_id:str; stage_id:str; attempt:int

@dataclass(frozen=True)
class LeaseToken:
    key:LeaseKey; worker_id:str; fencing_token:int; acquired_at:float; expires_at:float

class LeaseManager:
    def __init__(self,clock:Optional[Callable[[],float]]=None):
        self.clock=clock or time.time; self._active={}; self._gen={}
    def _now(self): return float(self.clock())
    def _expired(self,t): return self._now()>=t.expires_at
    def acquire(self,key,worker_id,ttl_seconds):
        cur=self._active.get(key)
        if cur is not None and not self._expired(cur): raise LeaseError("already leased")
        g=self._gen.get(key,0)+1; self._gen[key]=g
        n=self._now(); t=LeaseToken(key,worker_id,g,n,n+ttl_seconds); self._active[key]=t; return t
    def renew(self,token,ttl_seconds):
        self.commit_guard(token); n=self._now()
        t=LeaseToken(token.key,token.worker_id,token.fencing_token,token.acquired_at,n+ttl_seconds)
        self._active[token.key]=t; return t
    def commit_guard(self,token):
        cur=self._active.get(token.key)
        if cur is None: raise LeaseError("no lease")
        if cur.worker_id!=token.worker_id or cur.fencing_token!=token.fencing_token: raise LeaseError("stale token")
        if self._expired(cur): raise LeaseError("expired")
    def release(self,token):
        self.commit_guard(token); self._active.pop(token.key,None)
    def active_lease(self,key):
        cur=self._active.get(key)
        if cur is None or self._expired(cur): return None
        return cur

class WorkerOwnershipGuard:
    def __init__(self,leases): self.leases=leases
    def authorize_state_write(self,token,run_id,stage_id,attempt):
        if token.key!=LeaseKey(run_id,stage_id,attempt): raise LeaseError("scope mismatch")
        self.leases.commit_guard(token)
    def authorize_artifact_write(self,token,run_id,stage_id,attempt):
        self.authorize_state_write(token,run_id,stage_id,attempt)
