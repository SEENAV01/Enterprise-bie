
from dataclasses import dataclass
class QueueHealthError(ValueError): pass
@dataclass(frozen=True)
class QueueSnapshot:
 ready:int; delivered:int; dead_letter:int; oldest_ready_age:float
def classify(q):
 if min(q.ready,q.delivered,q.dead_letter)<0 or q.oldest_ready_age<0: raise QueueHealthError("invalid")
 if q.dead_letter>0:return "DEGRADED"
 if q.oldest_ready_age>300:return "BACKLOGGED"
 if q.ready>1000:return "BACKLOGGED"
 return "HEALTHY"
