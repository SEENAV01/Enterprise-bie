
from dataclasses import dataclass
class TimelineError(ValueError): pass
@dataclass(frozen=True)
class TimelineEvent:
 seq:int; run_id:str; stage_id:str|None; event:str; timestamp:float
class RunTimeline:
 def __init__(self): self.events=[]
 def add(self,run_id,event,timestamp,stage_id=None):
  if not run_id or not event: raise TimelineError("required")
  if self.events and timestamp<self.events[-1].timestamp: raise TimelineError("non-monotonic timestamp")
  x=TimelineEvent(len(self.events)+1,run_id,stage_id,event,timestamp);self.events.append(x);return x
 def for_run(self,run_id): return tuple(x for x in self.events if x.run_id==run_id)
