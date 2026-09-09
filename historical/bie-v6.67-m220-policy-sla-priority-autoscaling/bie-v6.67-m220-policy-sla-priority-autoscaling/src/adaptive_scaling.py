def scaling_decision(queue_depth,arrival_rate,service_rate,
                    workers,min_workers=1,max_workers=32,
                    target_utilization=0.75):
    if min_workers<1 or max_workers<min_workers or service_rate<=0:
        raise ValueError("INVALID_SCALING_CONFIG")
    desired=max(min_workers,
                int((arrival_rate/service_rate)/target_utilization+0.999999))
    desired=min(max_workers,desired)
    if queue_depth>0 and desired<max_workers:
        desired+=1
    desired=min(max_workers,desired)
    action="SCALE_OUT" if desired>workers else (
        "SCALE_IN" if desired<workers else "HOLD")
    return {"desired_workers":desired,"action":action,
            "target_utilization":target_utilization}
