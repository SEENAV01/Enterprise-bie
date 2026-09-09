
import hashlib
class ObjectStoreError(ValueError):pass
class ObjectStoreAdapter:
 def __init__(self,backend):self.b=backend
 def put(self,data):
  if not isinstance(data,(bytes,bytearray)):raise ObjectStoreError("bytes required")
  h=hashlib.sha256(data).hexdigest();self.b.put(h,bytes(data));return h
 def get(self,h):
  d=self.b.get(h)
  if d is None:raise ObjectStoreError("not found")
  if hashlib.sha256(d).hexdigest()!=h:raise ObjectStoreError("integrity failure")
  return d
