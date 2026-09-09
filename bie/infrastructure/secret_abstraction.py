
from dataclasses import dataclass
class SecretError(ValueError): pass
@dataclass(frozen=True)
class SecretRef: provider:str; name:str; version:str|None=None
class SecretResolver:
 def __init__(self,providers): self.providers=providers
 def resolve(self,ref):
  if ref.provider not in self.providers: raise SecretError("unknown provider")
  if not ref.name or any(x in ref.name.lower() for x in ("password=","sk-")): raise SecretError("invalid secret reference")
  value=self.providers[ref.provider](ref.name,ref.version)
  if value is None: raise SecretError("secret unavailable")
  return value
