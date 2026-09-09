def metric(metric_id,name,value,unit=None,dimensions=None,
           source_event_refs=None):
    return {"metric_id":metric_id,"name":name,"value":value,
            "unit":unit,"dimensions":dimensions or {},
            "source_event_refs":source_event_refs or []}

def aggregate(values,method="mean"):
    if not values: return None
    if method=="sum": return sum(values)
    if method=="min": return min(values)
    if method=="max": return max(values)
    return sum(values)/len(values)
