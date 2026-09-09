from dataclasses import dataclass, field
from typing import Set, Dict, List

class WorkerSchedulingError(ValueError): pass

@dataclass(frozen=True)
class WorkerCapabilities:
    worker_id:str; capabilities:Set[str]; cpu_cores:float; memory_gb:float
    max_concurrency:int=1

@dataclass(frozen=True)
class StageResourceRequirement:
    stage_id:str; required_capabilities:Set[str]
    min_cpu_cores:float=1.0; min_memory_gb:float=1.0; slot_cost:int=1

@dataclass(frozen=True)
class WorkerLoad:
    worker_id:str; active_slots:int=0; healthy:bool=True

@dataclass(frozen=True)
class WorkerSelection:
    stage_id:str; worker_id:str; score:tuple; reasons:List[str]

class CapabilityScheduler:
    def __init__(self,workers,loads=None):
        self.workers={w.worker_id:w for w in workers}; self.loads=dict(loads or {})
    def _load(self,wid): return self.loads.get(wid,WorkerLoad(wid))
    def select(self,req):
        cand=[]
        for w in self.workers.values():
            l=self._load(w.worker_id)
            if not l.healthy: continue
            if not req.required_capabilities.issubset(w.capabilities): continue
            if w.cpu_cores<req.min_cpu_cores or w.memory_gb<req.min_memory_gb: continue
            if l.active_slots+req.slot_cost>w.max_concurrency: continue
            cand.append((l.active_slots/w.max_concurrency,w.worker_id))
        if not cand: raise WorkerSchedulingError("no eligible worker")
        cand.sort()
        return WorkerSelection(req.stage_id,cand[0][1],cand[0],["eligible"])
    def reserve(self,sel,req):
        cur=self._load(sel.worker_id)
        self.loads[sel.worker_id]=WorkerLoad(sel.worker_id,cur.active_slots+req.slot_cost,cur.healthy)
    def release(self,worker_id,slot_cost=1):
        cur=self._load(worker_id)
        if cur.active_slots<slot_cost: raise WorkerSchedulingError("capacity underflow")
        self.loads[worker_id]=WorkerLoad(worker_id,cur.active_slots-slot_cost,cur.healthy)
