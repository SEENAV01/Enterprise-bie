from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

class WorkerSchedulingError(ValueError): pass

@dataclass(frozen=True)
class WorkerCapabilities:
    worker_id:str
    capabilities:Set[str]
    cpu_cores:float
    memory_gb:float
    gpu:bool=False
    gpu_vram_gb:float=0.0
    max_concurrency:int=1
    affinity_tags:Set[str]=field(default_factory=set)

    def validate(self):
        if not self.worker_id: raise WorkerSchedulingError("worker_id required")
        if self.cpu_cores<=0 or self.memory_gb<=0: raise WorkerSchedulingError("invalid worker resources")
        if self.max_concurrency<1: raise WorkerSchedulingError("max_concurrency must be >=1")
        if not self.gpu and self.gpu_vram_gb>0: raise WorkerSchedulingError("VRAM advertised without GPU")
        if self.gpu_vram_gb<0: raise WorkerSchedulingError("invalid gpu_vram")

@dataclass(frozen=True)
class StageResourceRequirement:
    stage_id:str
    required_capabilities:Set[str]
    min_cpu_cores:float=1.0
    min_memory_gb:float=1.0
    requires_gpu:bool=False
    min_gpu_vram_gb:float=0.0
    slot_cost:int=1
    preferred_affinity_tags:Set[str]=field(default_factory=set)
    requires_sandbox:bool=False

    def validate(self):
        if not self.stage_id: raise WorkerSchedulingError("stage_id required")
        if self.min_cpu_cores<=0 or self.min_memory_gb<=0: raise WorkerSchedulingError("invalid requirement resources")
        if self.slot_cost<1: raise WorkerSchedulingError("slot_cost must be >=1")
        if self.min_gpu_vram_gb<0: raise WorkerSchedulingError("invalid min_gpu_vram")
        if self.min_gpu_vram_gb>0 and not self.requires_gpu:
            raise WorkerSchedulingError("gpu_vram requirement requires GPU")

@dataclass(frozen=True)
class WorkerLoad:
    worker_id:str
    active_slots:int=0
    healthy:bool=True

    def validate(self):
        if not self.worker_id: raise WorkerSchedulingError("worker_id required")
        if self.active_slots<0: raise WorkerSchedulingError("active_slots cannot be negative")

@dataclass(frozen=True)
class WorkerSelection:
    stage_id:str
    worker_id:str
    score:tuple
    reasons:List[str]

class CapabilityScheduler:
    def __init__(self,workers:List[WorkerCapabilities],loads:Optional[Dict[str,WorkerLoad]]=None):
        self.workers={w.worker_id:w for w in workers}
        if len(self.workers)!=len(workers): raise WorkerSchedulingError("duplicate worker_id")
        for w in workers:w.validate()
        self.loads=dict(loads or {})
        for wid,l in self.loads.items():
            l.validate()
            if wid not in self.workers: raise WorkerSchedulingError("load references unknown worker")

    def _load(self,worker_id:str)->WorkerLoad:
        return self.loads.get(worker_id,WorkerLoad(worker_id,0,True))

    def eligible(self,w:WorkerCapabilities,req:StageResourceRequirement)->tuple[bool,List[str]]:
        req.validate()
        l=self._load(w.worker_id)
        reasons=[]
        if not l.healthy:return False,["worker unhealthy"]
        missing=sorted(req.required_capabilities-w.capabilities)
        if missing:return False,[f"missing capabilities: {','.join(missing)}"]
        if w.cpu_cores<req.min_cpu_cores:return False,["insufficient cpu"]
        if w.memory_gb<req.min_memory_gb:return False,["insufficient memory"]
        if req.requires_gpu and not w.gpu:return False,["gpu required"]
        if req.requires_gpu and w.gpu_vram_gb<req.min_gpu_vram_gb:return False,["insufficient gpu vram"]
        if l.active_slots+req.slot_cost>w.max_concurrency:return False,["concurrency capacity exceeded"]
        if req.requires_sandbox and "sandbox" not in w.capabilities:return False,["sandbox capability required"]
        reasons.append("all hard requirements satisfied")
        return True,reasons

    def select(self,req:StageResourceRequirement)->WorkerSelection:
        req.validate()
        candidates=[]
        rejection={}
        for w in self.workers.values():
            ok,reasons=self.eligible(w,req)
            if not ok:
                rejection[w.worker_id]=reasons
                continue
            load=self._load(w.worker_id)
            affinity=len(req.preferred_affinity_tags & w.affinity_tags)
            capability_extra=len(w.capabilities-req.required_capabilities)
            cpu_headroom=w.cpu_cores-req.min_cpu_cores
            mem_headroom=w.memory_gb-req.min_memory_gb
            gpu_headroom=(w.gpu_vram_gb-req.min_gpu_vram_gb) if req.requires_gpu else 0.0
            # Lower tuple is better. Prefer affinity, then lower load ratio, then
            # adequate-but-not-wasteful capability fit, then more headroom.
            load_ratio=(load.active_slots+req.slot_cost)/w.max_concurrency
            score=(-affinity,load_ratio,capability_extra,-cpu_headroom,-mem_headroom,-gpu_headroom,w.worker_id)
            reasons=list(reasons)+[
                f"affinity_matches={affinity}",
                f"load_ratio={load_ratio:.4f}",
                f"cpu_headroom={cpu_headroom:.2f}",
                f"memory_headroom={mem_headroom:.2f}"
            ]
            candidates.append((score,w,reasons))
        if not candidates:
            detail="; ".join(f"{k}: {','.join(v)}" for k,v in sorted(rejection.items()))
            raise WorkerSchedulingError(f"no eligible worker for {req.stage_id}. {detail}")
        candidates.sort(key=lambda x:x[0])
        score,w,reasons=candidates[0]
        return WorkerSelection(req.stage_id,w.worker_id,score,reasons)

    def reserve(self,selection:WorkerSelection,req:StageResourceRequirement)->WorkerLoad:
        if selection.worker_id not in self.workers: raise WorkerSchedulingError("unknown selected worker")
        w=self.workers[selection.worker_id]
        ok,_=self.eligible(w,req)
        if not ok: raise WorkerSchedulingError("worker no longer eligible at reservation")
        current=self._load(w.worker_id)
        new=WorkerLoad(w.worker_id,current.active_slots+req.slot_cost,current.healthy)
        self.loads[w.worker_id]=new
        return new

    def release(self,worker_id:str,slot_cost:int=1)->WorkerLoad:
        if slot_cost<1: raise WorkerSchedulingError("slot_cost must be >=1")
        current=self._load(worker_id)
        if current.active_slots<slot_cost: raise WorkerSchedulingError("cannot release more slots than active")
        new=WorkerLoad(worker_id,current.active_slots-slot_cost,current.healthy)
        self.loads[worker_id]=new
        return new

    def set_health(self,worker_id:str,healthy:bool)->None:
        if worker_id not in self.workers: raise WorkerSchedulingError("unknown worker")
        cur=self._load(worker_id)
        self.loads[worker_id]=WorkerLoad(worker_id,cur.active_slots,healthy)
