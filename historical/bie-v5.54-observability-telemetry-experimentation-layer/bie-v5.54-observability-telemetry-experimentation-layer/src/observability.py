def observability_record(events=None,metrics=None,traces=None,
                         costs=None,latencies=None,experiments=None):
    return {"events":events or [],"metrics":metrics or [],
            "traces":traces or [],"costs":costs or [],
            "latencies":latencies or [],
            "experiments":experiments or []}

def quality_summary(validation_events):
    total=len(validation_events)
    failed=sum(1 for e in validation_events
               if e.get("payload",{}).get("status")=="FAIL")
    return {"total":total,"failed":failed,
            "failure_rate":(failed/total if total else 0)}
