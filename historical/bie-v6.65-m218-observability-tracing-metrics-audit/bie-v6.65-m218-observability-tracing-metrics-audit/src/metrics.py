class Metrics:
    def __init__(self): self.counters={}; self.gauges={}; self.histograms={}
    def inc(self,name,value=1,tags=None):
        self.counters[name]=self.counters.get(name,0)+value
    def set(self,name,value,tags=None): self.gauges[name]=value
    def observe(self,name,value,tags=None):
        self.histograms.setdefault(name,[]).append(value)
    def snapshot(self):
        return {"counters":self.counters,"gauges":self.gauges,
                "histograms":self.histograms}
