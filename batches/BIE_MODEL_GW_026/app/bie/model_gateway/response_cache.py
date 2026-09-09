
from dataclasses import dataclass
class CacheError(ValueError):pass
@dataclass
class Entry:value:object;expires_at:float
class ResponseCache:
 def __init__(self):self.x={}
 def put(self,key,value,expires_at):
  if not key:raise CacheError("key");self.x[key]=Entry(value,expires_at)
  self.x[key]=Entry(value,expires_at)
 def get(self,key,now):
  e=self.x.get(key)
  if not e:return None
  if now>=e.expires_at:self.x.pop(key,None);return None
  return e.value
