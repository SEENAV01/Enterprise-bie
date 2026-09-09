
from dataclasses import dataclass
from datetime import datetime,timezone
class HistoryError(ValueError): pass
@dataclass(frozen=True)
class TaskEvent:
 seq:int; task_id:str; event_type:str; status:str; actor:str; evidence_refs:tuple; timestamp:str
class ExecutionHistory:
 def __init__(self): self.events=[]
 def append(self,task_id,event_type,status,actor,evidence_refs=(),timestamp=None):
  if not task_id or not event_type or not actor: raise HistoryError("required field missing")
  ts=timestamp or datetime.now(timezone.utc).isoformat()
  ev=TaskEvent(len(self.events)+1,task_id,event_type,status,actor,tuple(evidence_refs),ts)
  self.events.append(ev); return ev
 def for_task(self,task_id): return tuple(e for e in self.events if e.task_id==task_id)
 def latest(self,task_id):
  xs=self.for_task(task_id)
  return xs[-1] if xs else None
