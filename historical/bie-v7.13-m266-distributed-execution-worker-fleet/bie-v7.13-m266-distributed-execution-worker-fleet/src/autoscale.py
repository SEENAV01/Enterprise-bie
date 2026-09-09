def desired_workers(queue_depth, worker_capacity, target_utilization=0.75):
    if worker_capacity<=0: return 0
    return max(1,int((queue_depth/(worker_capacity*target_utilization))+0.9999))

def scaling_action(current, desired):
    if desired>current: return "SCALE_OUT"
    if desired<current: return "SCALE_IN"
    return "HOLD"
