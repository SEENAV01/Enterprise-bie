
from dataclasses import dataclass
import time
class ReplayError(RuntimeError): pass
@dataclass(frozen=True)
class ReplayToken:
 token_id:str; scope:str; issued_at:float; expires_at:float
class ReplayProtector:
 def __init__(self,clock=time.time): self.clock=clock; self.used={}
 def validate_and_consume(self,t:ReplayToken,expected_scope:str):
  now=self.clock()
  if not t.token_id or not t.scope: raise ReplayError("invalid token")
  if t.scope!=expected_scope: raise ReplayError("scope mismatch")
  if t.issued_at>now: raise ReplayError("token issued in future")
  if t.expires_at<=now: raise ReplayError("token expired")
  if t.token_id in self.used: raise ReplayError("replay detected")
  self.used[t.token_id]=(t.scope,now)
  return True
 def consumed(self,token_id): return token_id in self.used
