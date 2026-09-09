
from dataclasses import dataclass
class CompatibilityError(ValueError): pass
@dataclass(frozen=True)
class CompatibilityRule:
 component:str; min_schema:int; max_schema:int
class CompatibilityMatrix:
 def __init__(self,rules): self.rules={r.component:r for r in rules}
 def check(self,component,schema_version):
  if component not in self.rules: raise CompatibilityError("unknown component")
  r=self.rules[component]
  return r.min_schema<=schema_version<=r.max_schema
 def assert_compatible(self,component,schema_version):
  if not self.check(component,schema_version): raise CompatibilityError(f"{component} incompatible with schema {schema_version}")
  return True
 def common_versions(self,components):
  rs=[self.rules[c] for c in components if c in self.rules]
  if len(rs)!=len(components): raise CompatibilityError("unknown component")
  lo=max(r.min_schema for r in rs); hi=min(r.max_schema for r in rs)
  return list(range(lo,hi+1)) if lo<=hi else []
