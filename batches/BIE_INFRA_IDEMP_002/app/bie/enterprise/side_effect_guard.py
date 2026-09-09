
import hashlib,json
class SideEffectError(RuntimeError): pass
def fingerprint(operation:str,payload:dict)->str:
 if not operation: raise SideEffectError("operation required")
 return hashlib.sha256((operation+"|"+json.dumps(payload,sort_keys=True,separators=(",",":"))).encode()).hexdigest()
class SideEffectGuard:
 def __init__(self,claim_store): self.store=claim_store
 def begin(self,key,operation,payload,owner):
  fp=fingerprint(operation,payload); c=self.store.claim(key,fp,owner)
  if c.state=="COMPLETED": return {"execute":False,"result_ref":c.result_ref,"fingerprint":fp}
  if c.owner!=owner: raise SideEffectError("claim owned by another worker")
  return {"execute":True,"result_ref":None,"fingerprint":fp}
 def commit(self,key,owner,result_ref): return self.store.complete(key,owner,result_ref)
