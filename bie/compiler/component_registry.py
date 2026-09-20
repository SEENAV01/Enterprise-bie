from __future__ import annotations
from dataclasses import dataclass
import re

class ComponentRegistryError(ValueError):
    pass

_TS_IDENT=re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

@dataclass(frozen=True)
class ComponentSpec:
    component_id:str
    element_type:str
    component_name:str
    import_path:str
    capability_id:str
    profiles:tuple[str,...]
    prop_keys:tuple[str,...]=()
    priority:int=100

    def __post_init__(self):
        for name in ("component_id","element_type","component_name","import_path","capability_id"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise ComponentRegistryError(f"{name} invalid")
        if not _TS_IDENT.fullmatch(self.component_name):
            raise ComponentRegistryError("component_name is not a valid TS identifier")
        if "://" in self.import_path or self.import_path.startswith("/"):
            raise ComponentRegistryError("import_path must be package/relative, not URL/absolute")
        if not self.profiles:
            raise ComponentRegistryError("profiles required")
        object.__setattr__(self,"profiles",tuple(self.profiles))
        object.__setattr__(self,"prop_keys",tuple(sorted(set(self.prop_keys))))
        if isinstance(self.priority,bool) or not isinstance(self.priority,int):
            raise ComponentRegistryError("priority must be int")

class ComponentRegistry:
    def __init__(self):
        self._items={}

    def register(self,spec):
        if spec.component_id in self._items:
            raise ComponentRegistryError("duplicate component_id")
        self._items[spec.component_id]=spec
        return True

    def resolve(self, element_type, profile):
        candidates=[
            s for s in self._items.values()
            if s.element_type==element_type and profile in s.profiles
        ]
        candidates.sort(key=lambda s:(s.priority,s.component_id))
        return candidates[0] if candidates else None

    def require(self,element_type,profile):
        spec=self.resolve(element_type,profile)
        if spec is None:
            raise ComponentRegistryError(f"no component for {element_type}/{profile}")
        return spec

    def snapshot(self):
        return tuple(sorted(
            (s.component_id,s.element_type,s.component_name,s.import_path,s.capability_id,s.profiles,s.prop_keys,s.priority)
            for s in self._items.values()
        ))
