def sli(name,good_events,total_events,
         window=None,unit="ratio"):
    ratio=(good_events/total_events
           if total_events else 1.0)
    return {"name":name,"good_events":good_events,
            "total_events":total_events,
            "value":ratio,"window":window,
            "unit":unit}

def error_rate(good_events,total_events):
    return 0 if total_events==0 else 1-good_events/total_events
