
from dataclasses import dataclass,asdict
import hashlib,json
class AuditError(ValueError):pass
@dataclass(frozen=True)
class AuditEntry:
 seq:int;actor:str;action:str;resource:str;timestamp:float;prev_hash:str;entry_hash:str
class AuditLog:
 def __init__(self):self.entries=[]
 def append(self,actor,action,resource,timestamp):
  if not actor or not action or not resource:raise AuditError("required")
  prev=self.entries[-1].entry_hash if self.entries else "GENESIS"
  payload={"seq":len(self.entries)+1,"actor":actor,"action":action,"resource":resource,"timestamp":timestamp,"prev_hash":prev}
  h=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
  e=AuditEntry(**payload,entry_hash=h);self.entries.append(e);return e
 def verify(self):
  prev="GENESIS"
  for i,e in enumerate(self.entries,1):
   p={"seq":i,"actor":e.actor,"action":e.action,"resource":e.resource,"timestamp":e.timestamp,"prev_hash":prev}
   h=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest()
   if e.seq!=i or e.prev_hash!=prev or e.entry_hash!=h:return False
   prev=e.entry_hash
  return True
