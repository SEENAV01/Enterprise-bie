
from dataclasses import dataclass
class APIError(ValueError):pass
@dataclass(frozen=True)
class CreateRunRequest: source_ref:str; config_hash:str
@dataclass(frozen=True)
class RunView: run_id:str; status:str; source_ref:str; config_hash:str
class RunAPI:
 def __init__(self,store):self.store=store
 def create(self,req):
  if not req.source_ref or len(req.config_hash)!=64:raise APIError("invalid request")
  return self.store.create(req)
 def get(self,run_id):
  x=self.store.get(run_id)
  if x is None:raise APIError("run not found")
  return x
 def list(self):return tuple(self.store.list())
