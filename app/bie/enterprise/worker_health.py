
from dataclasses import dataclass
class WorkerHealthError(ValueError): pass
@dataclass(frozen=True)
class WorkerHeartbeat:
 worker_id:str; timestamp:float; active_tasks:int; capacity:int; error_rate:float
def classify(h,now,stale_after=60):
 if not h.worker_id or h.capacity<1 or h.active_tasks<0 or h.error_rate<0: raise WorkerHealthError("invalid heartbeat")
 if now-h.timestamp>stale_after:return "STALE"
 if h.active_tasks>h.capacity:return "OVERLOADED"
 if h.error_rate>=0.5:return "DEGRADED"
 return "HEALTHY"
