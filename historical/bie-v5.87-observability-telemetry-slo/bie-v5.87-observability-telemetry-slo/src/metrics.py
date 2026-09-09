def counter(name,labels=None):
    return {"type":"counter","name":name,
            "labels":labels or {},"value":0}

def increment(metric,value=1):
    out=dict(metric); out["value"]=metric["value"]+value
    return out

def gauge(name,value,labels=None):
    return {"type":"gauge","name":name,
            "labels":labels or {},"value":value}

def histogram(name,values,labels=None):
    vals=list(values)
    return {"type":"histogram","name":name,
            "labels":labels or {},"count":len(vals),
            "sum":sum(vals),"min":min(vals) if vals else None,
            "max":max(vals) if vals else None}
