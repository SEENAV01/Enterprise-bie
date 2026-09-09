
from dataclasses import dataclass
class EventStreamError(ValueError):pass
@dataclass(frozen=True)
class StreamEvent: seq:int; run_id:str; event_type:str; payload:dict
class EventStream:
 def __init__(self,max_events=1000):self.max=max_events;self.events=[]
 def publish(self,run_id,event_type,payload):
  if not run_id or not event_type:raise EventStreamError("required")
  e=StreamEvent((self.events[-1].seq+1) if self.events else 1,run_id,event_type,dict(payload));self.events.append(e)
  if len(self.events)>self.max:self.events=self.events[-self.max:]
  return e
 def since(self,seq,run_id=None):
  return tuple(e for e in self.events if e.seq>seq and (run_id is None or e.run_id==run_id))
