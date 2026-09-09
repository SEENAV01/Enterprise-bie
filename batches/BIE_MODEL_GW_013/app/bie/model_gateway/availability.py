
from dataclasses import dataclass
class AvailabilityError(ValueError):pass
@dataclass(frozen=True)
class Health:provider:str;model:str;available:bool;latency_ms:float;checked_at:float
def usable(h,max_latency_ms=None):
 if h.latency_ms<0:raise AvailabilityError("latency")
 return h.available and (max_latency_ms is None or h.latency_ms<=max_latency_ms)
def choose(healths):
 xs=[h for h in healths if usable(h)]
 if not xs:raise AvailabilityError("no available model")
 return min(xs,key=lambda h:h.latency_ms)
