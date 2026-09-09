
from dataclasses import dataclass,asdict
import hashlib,json
class AuditError(ValueError):pass
@dataclass(frozen=True)
class GatewayAuditEvent:
 seq:int;request_id:str;event_type:str;provider:str|None;model:str|None;decision_id:str|None;timestamp:float;prev_hash:str;event_hash:str
class GatewayAudit:
 def __init__(self):self.events=[]
 def append(self,request_id,event_type,timestamp,provider=None,model=None,decision_id=None):
  if not request_id or not event_type:raise AuditError("required")
  prev=self.events[-1].event_hash if self.events else "GENESIS"
  d={"seq":len(self.events)+1,"request_id":request_id,"event_type":event_type,"provider":provider,"model":model,"decision_id":decision_id,"timestamp":timestamp,"prev_hash":prev}
  h=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest()
  e=GatewayAuditEvent(**d,event_hash=h);self.events.append(e);return e
 def verify(self):
  prev="GENESIS"
  for i,e in enumerate(self.events,1):
   d={"seq":i,"request_id":e.request_id,"event_type":e.event_type,"provider":e.provider,"model":e.model,"decision_id":e.decision_id,"timestamp":e.timestamp,"prev_hash":prev}
   h=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest()
   if e.seq!=i or e.prev_hash!=prev or e.event_hash!=h:return False
   prev=e.event_hash
  return True
