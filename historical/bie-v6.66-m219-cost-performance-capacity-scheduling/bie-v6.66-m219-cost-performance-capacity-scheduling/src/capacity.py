def capacity_forecast(arrival_rate,service_rate,workers):
    capacity=service_rate*workers
    utilization=arrival_rate/capacity if capacity else 1
    return {"arrival_rate":arrival_rate,"service_rate":service_rate,
            "workers":workers,"capacity":capacity,
            "utilization":utilization,
            "headroom":max(0,1-utilization)}

def required_workers(arrival_rate,service_rate,target_utilization=0.75):
    if service_rate<=0 or not 0<target_utilization<=1:
        raise ValueError("INVALID_CAPACITY_INPUT")
    n=1
    while n*service_rate*target_utilization < arrival_rate: n+=1
    return n
