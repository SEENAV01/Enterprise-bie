def autoscaling_policy(resource,
                       min_instances,
                       max_instances,
                       target_utilization):
    return {"resource":resource,
            "min_instances":min_instances,
            "max_instances":max_instances,
            "target_utilization":target_utilization}

def desired_instances(policy,utilization,
                       current_instances):
    if utilization > policy["target_utilization"]:
        return min(policy["max_instances"],
                   current_instances+1)
    if utilization < policy["target_utilization"]*.5:
        return max(policy["min_instances"],
                   current_instances-1)
    return current_instances
