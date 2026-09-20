from dataclasses import dataclass
from .capability_common import *

@dataclass(frozen=True)
class CompilerCapability:
    capability_id:str
    version:str
    element_types:tuple[str,...]
    actions:tuple[str,...]
    profiles:tuple[str,...]
    deterministic:bool=True
    def __post_init__(self):
        object.__setattr__(self,'capability_id',tok(self.capability_id,'capability_id'))
        object.__setattr__(self,'version',tok(self.version,'version'))
        object.__setattr__(self,'element_types',ids(self.element_types,'element_types'))
        object.__setattr__(self,'actions',ids(self.actions,'actions',allow_empty=True))
        object.__setattr__(self,'profiles',ids(self.profiles,'profiles'))

class CapabilityRegistry:
    def __init__(self): self._caps={}
    def register(self,c):
        if c.capability_id in self._caps: raise SceneIRCapabilityError('duplicate capability')
        self._caps[c.capability_id]=c; return True
    def supports(self,cid,element_type=None,action=None,profile=None):
        c=self._caps.get(cid)
        if c is None: return False
        if element_type is not None and element_type not in c.element_types: return False
        if action is not None and action not in c.actions: return False
        if profile is not None and profile not in c.profiles: return False
        return True
    def snapshot(self):
        return tuple(sorted((c.capability_id,c.version,c.element_types,c.actions,c.profiles,c.deterministic) for c in self._caps.values()))
