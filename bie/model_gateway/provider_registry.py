
from dataclasses import dataclass
class RegistryError(ValueError):pass
@dataclass(frozen=True)
class ProviderDescriptor:
 provider_id:str;model_id:str;capabilities:frozenset;enabled:bool=True
class ProviderRegistry:
 def __init__(self):self.x={}
 def register(self,d,adapter):
  k=(d.provider_id,d.model_id)
  if not all(k) or k in self.x:raise RegistryError("invalid/duplicate provider model")
  self.x[k]=(d,adapter)
 def candidates(self,required):
  return tuple((d,a) for d,a in self.x.values() if d.enabled and set(required).issubset(d.capabilities))
 def get(self,p,m):
  if (p,m) not in self.x:raise RegistryError("not found")
  return self.x[(p,m)]
