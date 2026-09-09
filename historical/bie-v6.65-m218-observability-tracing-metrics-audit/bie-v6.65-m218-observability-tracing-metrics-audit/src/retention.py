def retention_policy(log_days=30,trace_days=14,audit_days=365):
    return {"log_days":log_days,"trace_days":trace_days,
            "audit_days":audit_days}
def valid(p): return all(isinstance(p[x],int) and p[x]>=0
    for x in p)
