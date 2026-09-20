from __future__ import annotations
from dataclasses import dataclass

class CompilerCapabilityRegistryError(ValueError):
    pass

@dataclass(frozen=True)
class CompilerAdapterCapability:
    capability_id:str
    adapter_id:str
    version:str
    element_types:tuple[str,...]
    actions:tuple[str,...]
    profiles:tuple[str,...]
    priority:int=100
    deterministic:bool=True

    def __post_init__(self):
        for name in ("capability_id","adapter_id","version"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise CompilerCapabilityRegistryError(f"{name} invalid")
        for name in ("element_types","profiles"):
            vals=tuple(getattr(self,name))
            if not vals or any(not isinstance(x,str) or not x.strip() for x in vals):
                raise CompilerCapabilityRegistryError(f"{name} invalid")
            object.__setattr__(self,name,vals)
        object.__setattr__(self,"actions",tuple(self.actions))
        if isinstance(self.priority,bool) or not isinstance(self.priority,int):
            raise CompilerCapabilityRegistryError("priority must be int")

class CompilerCapabilityRegistry:
    def __init__(self):
        self._items={}

    def register(self,capability):
        key=(capability.capability_id,capability.adapter_id,capability.version)
        if key in self._items:
            raise CompilerCapabilityRegistryError("duplicate capability registration")
        self._items[key]=capability
        return True

    def resolve(self, *, element_type, action, profile):
        candidates=[]
        for cap in self._items.values():
            if element_type not in cap.element_types:
                continue
            if action is not None and action not in cap.actions:
                continue
            if profile not in cap.profiles:
                continue
            candidates.append(cap)
        candidates.sort(key=lambda c:(c.priority,c.adapter_id,c.version,c.capability_id))
        return candidates[0] if candidates else None

    def require(self, **kwargs):
        value=self.resolve(**kwargs)
        if value is None:
            raise CompilerCapabilityRegistryError("no compiler capability satisfies request")
        return value

    def snapshot(self):
        return tuple(
            sorted(
                (
                    c.capability_id,c.adapter_id,c.version,c.element_types,
                    c.actions,c.profiles,c.priority,c.deterministic
                )
                for c in self._items.values()
            )
        )
