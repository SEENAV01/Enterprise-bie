from dataclasses import dataclass

class DomainRegistryError(ValueError): pass

@dataclass(frozen=True)
class DomainAdapter:
    adapter_id:str
    domain:str
    version:str
    capabilities:tuple[str,...]
    priority:int
    provider_neutral:bool=True

class DomainAnimationRegistry:
    def __init__(self):
        self._adapters={}
    def register(self,adapter):
        if not adapter.adapter_id or not adapter.domain or not adapter.version or not adapter.capabilities:
            raise DomainRegistryError("adapter metadata incomplete")
        key=(adapter.domain,adapter.adapter_id)
        if key in self._adapters:
            raise DomainRegistryError("duplicate adapter")
        self._adapters[key]=adapter
        return True
    def resolve(self,domain,capability):
        matches=[a for (d,_),a in self._adapters.items() if d==domain and capability in a.capabilities]
        if not matches:
            raise DomainRegistryError("no adapter for domain/capability")
        matches.sort(key=lambda a:(-a.priority,a.adapter_id))
        return matches[0]
    def snapshot(self):
        return tuple(sorted(
            (a.domain,a.adapter_id,a.version,a.capabilities,a.priority,a.provider_neutral)
            for a in self._adapters.values()
        ))
