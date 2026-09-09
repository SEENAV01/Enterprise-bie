
from dataclasses import dataclass,asdict
import json,time
class LogError(ValueError): pass
@dataclass(frozen=True)
class LogEvent:
 timestamp:float; level:str; event:str; run_id:str; stage_id:str|None; fields:dict
def make_log(level,event,run_id,stage_id=None,**fields):
 if level not in {"DEBUG","INFO","WARN","ERROR","CRITICAL"}: raise LogError("bad level")
 if not event or not run_id: raise LogError("event/run required")
 forbidden={"password","secret","token","api_key"}
 if forbidden.intersection(k.lower() for k in fields): raise LogError("sensitive field")
 return LogEvent(time.time(),level,event,run_id,stage_id,fields)
def encode(e): return json.dumps(asdict(e),sort_keys=True,separators=(",",":"))
