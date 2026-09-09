
class MetricError(ValueError): pass
class Metrics:
 def __init__(self): self.counters={};self.gauges={};self.histograms={}
 def inc(self,name,value=1):
  if value<0: raise MetricError("counter cannot decrement")
  self.counters[name]=self.counters.get(name,0)+value
 def gauge(self,name,value): self.gauges[name]=value
 def observe(self,name,value):
  if value<0: raise MetricError("negative observation")
  self.histograms.setdefault(name,[]).append(value)
 def snapshot(self): return {"counters":dict(self.counters),"gauges":dict(self.gauges),"histograms":{k:tuple(v) for k,v in self.histograms.items()}}
