
from dataclasses import dataclass
class FeatureFlagError(ValueError): pass
@dataclass(frozen=True)
class FeatureFlag:
    name:str
    enabled:bool
    reason:str
    owner:str
class FeatureFlags:
    def __init__(self, flags=()):
        self._flags={}
        for f in flags: self.set(f)
    def set(self,f:FeatureFlag):
        if not f.name.strip() or not f.owner.strip() or not f.reason.strip(): raise FeatureFlagError("name/owner/reason required")
        if f.name in self._flags: raise FeatureFlagError("duplicate flag")
        self._flags[f.name]=f
    def enabled(self,name,default=False):
        return self._flags[name].enabled if name in self._flags else default
    def snapshot(self):
        return {k:{"enabled":v.enabled,"reason":v.reason,"owner":v.owner} for k,v in sorted(self._flags.items())}
