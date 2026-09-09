
from dataclasses import dataclass
class ToolRegistryError(ValueError):pass
@dataclass(frozen=True)
class ToolDescriptor:name:str;version:str;capabilities:frozenset;side_effecting:bool=False
class ToolRegistry:
 def __init__(self):self.x={}
 def register(self,d,handler):
  k=(d.name,d.version)
  if not d.name or not d.version or k in self.x:raise ToolRegistryError("invalid/duplicate")
  self.x[k]=(d,handler)
 def resolve(self,name,version,allowed_capabilities):
  if (name,version) not in self.x:raise ToolRegistryError("not found")
  d,h=self.x[(name,version)]
  if not d.capabilities.issubset(set(allowed_capabilities)):raise ToolRegistryError("capability denied")
  return d,h
