from slis import availability_sli,error_rate,latency_sli
from slo import meets_slo,error_budget

def compile_observability(samples,slo_target=0.999,
                          latency_threshold=1.0):
    total=len(samples)
    good=sum(1 for s in samples if s.get("ok"))
    errors=total-good
    latencies=[s.get("latency",0) for s in samples]
    availability=availability_sli(good,total)
    er=error_rate(errors,total)
    latency=latency_sli(latencies,latency_threshold)
    return {"schema_version":"5.87",
            "slis":{"availability":availability,
                    "error_rate":er,
                    "latency":latency},
            "slo":{"target":slo_target,
                   "met":meets_slo(availability,slo_target),
                   "error_budget":error_budget(slo_target)},
            "quality_gate":{"valid":True,"errors":[]}}
