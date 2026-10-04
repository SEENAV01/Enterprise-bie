"""Bounded same-process, same-intent run-creation coordination.

This is NOT a queue, distributed lock, retry engine, durable result cache or
replacement for SQLite idempotency. Only overlapping exact requests coalesce.
SQLite still enforces cross-process identity with its unchanged one-second
busy timeout. Exhaustion/timeout fails closed; the owner is never cancelled.
"""
from copy import deepcopy
import os
from threading import Event, Lock
from weakref import WeakValueDictionary
from .contracts import OperatorError, require

class _Flight:
    def __init__(self):
        self.done=Event();self.result=None;self.error=None

class CreationAdmission:
    def __init__(self,wait_seconds=10.0,max_owners=32,max_waiters=64):
        require(type(wait_seconds) in (int,float) and 0<wait_seconds<=10,'invalid_admission_limit')
        require(type(max_owners) is int and 0<max_owners<=32 and
                type(max_waiters) is int and 0<max_waiters<=64,'invalid_admission_limit')
        self.wait_seconds=wait_seconds;self.max_owners=max_owners;self.max_waiters=max_waiters
        self._lock=Lock();self._flights={};self._waiters=0

    def run(self,key,operation):
        """Return (committed owner result, coalesced), never cache after overlap."""
        with self._lock:
            flight=self._flights.get(key);owner=flight is None
            if owner:
                require(len(self._flights)<self.max_owners,'creation_admission_full',503)
                flight=_Flight();self._flights[key]=flight
            else:
                require(self._waiters<self.max_waiters,'creation_admission_full',503)
                self._waiters+=1
        if not owner:
            try:
                require(flight.done.wait(self.wait_seconds),'creation_admission_timeout',503)
                if flight.error:raise OperatorError(*flight.error) from None
                return deepcopy(flight.result),True
            finally:
                with self._lock:self._waiters-=1
        try:
            result=operation();flight.result=deepcopy(result)
            return result,False
        except BaseException as exc:
            # Followers never receive another thread's traceback/exception text.
            flight.error=(exc.code,exc.status) if isinstance(exc,OperatorError) else ('internal_error',500)
            raise
        finally:
            with self._lock:
                flight.done.set();self._flights.pop(key,None)

_ROOTS=WeakValueDictionary()
_ROOT_LOCK=Lock()

def for_root(root):
    # Service has already validated/confined the root. Weak values retain no
    # abandoned root catalogues or unbounded historical request keys.
    key=os.path.normcase(str(root.resolve()))
    with _ROOT_LOCK:
        admission=_ROOTS.get(key)
        if admission is None:
            admission=CreationAdmission();_ROOTS[key]=admission
        return admission
