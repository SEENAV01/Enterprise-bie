
class LatencyError(ValueError): pass
class StageLatency:
 def __init__(self): self.samples={}
 def record(self,stage_id,seconds):
  if not stage_id or seconds<0: raise LatencyError("invalid sample")
  self.samples.setdefault(stage_id,[]).append(float(seconds))
 def summary(self,stage_id):
  xs=self.samples.get(stage_id,[])
  if not xs:return {"count":0,"min":None,"max":None,"avg":None}
  return {"count":len(xs),"min":min(xs),"max":max(xs),"avg":sum(xs)/len(xs)}
