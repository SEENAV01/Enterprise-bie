def resource(service,resource_id,
             kind,capacity,unit,
             current=0):
    return {"service":service,
            "resource_id":resource_id,
            "kind":kind,
            "capacity":capacity,
            "unit":unit,
            "current":current}

def utilization(record):
    cap=record.get("capacity",0)
    return 0 if cap<=0 else record.get("current",0)/cap
