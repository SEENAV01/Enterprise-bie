from dataclasses import dataclass
@dataclass(frozen=True)
class Binding:
 symbol:str; meaning:str; scope:str; source:str
class ScopeTable:
 def __init__(self):self._bindings=[]
 def bind(self,b:Binding):
  self._bindings.append(b)
 def resolve(self,symbol:str,scope_chain:list[str]):
  for scope in scope_chain:
   for b in reversed(self._bindings):
    if b.symbol==symbol and b.scope==scope:return b
  return None
 def conflicts(self):
  seen={};out=[]
  for b in self._bindings:
   k=(b.scope,b.symbol)
   if k in seen and seen[k]!=b.meaning:out.append(k)
   seen[k]=b.meaning
  return tuple(sorted(set(out)))
