
from dataclasses import dataclass
class AutoscaleError(ValueError):pass
@dataclass(frozen=True)
class ScalePolicy:
 min_workers:int;max_workers:int;target_queue_per_worker:float;cooldown_seconds:int
def desired(policy,ready,current):
 if policy.min_workers<0 or policy.max_workers<policy.min_workers or policy.target_queue_per_worker<=0:raise AutoscaleError("invalid policy")
 import math
 want=policy.min_workers if ready==0 else math.ceil(ready/policy.target_queue_per_worker)
 want=max(policy.min_workers,min(policy.max_workers,want))
 return want
