
class BenchmarkAPIError(ValueError):pass
class BenchmarkAPI:
 def __init__(self,registry,runner):self.registry=registry;self.runner=runner
 def cases(self,domain=None):
  xs=list(self.registry.cases())
  return tuple(x for x in xs if domain is None or x.get("domain")==domain)
 def run(self,case_id,artifact_refs):
  if not artifact_refs:raise BenchmarkAPIError("artifacts required")
  if self.registry.get(case_id) is None:raise BenchmarkAPIError("case not found")
  return self.runner.run(case_id,tuple(artifact_refs))
