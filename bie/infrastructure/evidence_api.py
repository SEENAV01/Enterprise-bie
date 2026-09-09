
class EvidenceAPIError(ValueError):pass
class EvidenceAPI:
 def __init__(self,store):self.s=store
 def get(self,ref):
  x=self.s.get(ref)
  if x is None:raise EvidenceAPIError("evidence not found")
  return x
 def for_run(self,run_id):return tuple(self.s.for_run(run_id))
 def for_gate(self,run_id,gate):return tuple(x for x in self.s.for_run(run_id) if x.get("gate")==gate)
