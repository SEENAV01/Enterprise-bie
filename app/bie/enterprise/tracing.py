
from dataclasses import dataclass
import time,uuid
class TraceError(ValueError): pass
@dataclass
class Span:
 trace_id:str; span_id:str; parent_id:str|None; name:str; start:float; end:float|None=None; status:str="OPEN"
class Tracer:
 def __init__(self): self.spans={}
 def start(self,name,trace_id=None,parent_id=None):
  if not name: raise TraceError("name")
  if parent_id and parent_id not in self.spans: raise TraceError("unknown parent")
  if parent_id: trace_id=self.spans[parent_id].trace_id
  s=Span(trace_id or uuid.uuid4().hex,uuid.uuid4().hex,parent_id,name,time.time());self.spans[s.span_id]=s;return s
 def finish(self,span_id,status="OK"):
  if status not in {"OK","ERROR"}: raise TraceError("status")
  s=self.spans[span_id]
  if s.end is not None: raise TraceError("already finished")
  s.end=time.time();s.status=status;return s
