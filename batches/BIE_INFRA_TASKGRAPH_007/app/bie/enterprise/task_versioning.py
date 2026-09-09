
from dataclasses import dataclass
import hashlib,json
class VersionError(ValueError): pass
@dataclass(frozen=True)
class TaskVersion:
 task_id:str; version:int; spec_hash:str; supersedes:int|None; change_reason:str
def spec_hash(spec:dict):
 return hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
class VersionLedger:
 def __init__(self): self._v={}
 def create(self,task_id,spec):
  if task_id in self._v: raise VersionError("task exists")
  v=TaskVersion(task_id,1,spec_hash(spec),None,"initial")
  self._v[task_id]=[v]; return v
 def revise(self,task_id,spec,reason):
  if task_id not in self._v: raise VersionError("unknown task")
  if not reason.strip(): raise VersionError("reason required")
  old=self._v[task_id][-1]; h=spec_hash(spec)
  if h==old.spec_hash: raise VersionError("no semantic spec change")
  v=TaskVersion(task_id,old.version+1,h,old.version,reason); self._v[task_id].append(v); return v
 def history(self,task_id): return tuple(self._v.get(task_id,()))
