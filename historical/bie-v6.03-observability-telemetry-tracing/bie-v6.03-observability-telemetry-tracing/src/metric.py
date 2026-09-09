def metric(name,value,timestamp,
           labels=None,unit=None):
    return {"name":name,"value":value,
            "timestamp":timestamp,
            "labels":labels or {},"unit":unit}

def counter(name,value=1,**kwargs):
    return metric(name,value,kwargs.pop("timestamp",0),
                  kwargs.pop("labels",{}),
                  kwargs.pop("unit",None))
