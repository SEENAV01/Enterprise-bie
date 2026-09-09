
from dataclasses import dataclass
import hashlib
class PromptError(ValueError):pass
@dataclass(frozen=True)
class PromptTemplate:name:str;version:str;template:str
def fingerprint(p):
 if not p.name or not p.version or not p.template:raise PromptError("incomplete prompt")
 return hashlib.sha256((p.name+"\0"+p.version+"\0"+p.template).encode()).hexdigest()
class PromptRegistry:
 def __init__(self):self.x={}
 def add(self,p):
  k=(p.name,p.version)
  if k in self.x:raise PromptError("immutable version exists")
  fingerprint(p);self.x[k]=p
 def get(self,n,v):
  if (n,v) not in self.x:raise PromptError("not found")
  return self.x[(n,v)]
