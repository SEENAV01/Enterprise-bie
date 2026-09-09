
class ReleaseAPIError(ValueError):pass
class ReleaseAPI:
 def __init__(self,evaluator,manifests):self.e=evaluator;self.m=manifests
 def evaluate(self,run_id):
  result=self.e.evaluate(run_id)
  if "passed" not in result or "gate_results" not in result:raise ReleaseAPIError("invalid evaluation")
  return result
 def certify(self,run_id):
  r=self.evaluate(run_id)
  if not r["passed"]:raise ReleaseAPIError("release blocked")
  return self.m.create(run_id,r)
 def get(self,run_id):
  x=self.m.get(run_id)
  if x is None:raise ReleaseAPIError("manifest not found")
  return x
