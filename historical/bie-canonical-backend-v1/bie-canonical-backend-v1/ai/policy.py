def choose_policy(task, policies):
    candidates=[p for p in policies if p["task_type"]==task["task_type"]]
    return max(candidates,key=lambda p:p.get("priority",0)) if candidates else None

def budget_allows(policy, estimated_cost, spent):
    return spent+estimated_cost <= policy.get("budget",float("inf"))

def latency_allows(policy, estimated_latency):
    limit=policy.get("max_latency")
    return limit is None or estimated_latency<=limit
