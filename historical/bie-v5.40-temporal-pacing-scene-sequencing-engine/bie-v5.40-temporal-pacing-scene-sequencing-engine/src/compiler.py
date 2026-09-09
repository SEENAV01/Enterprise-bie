from dependencies import topological_order

def compile_timeline(beats,dependencies,timing_constraints=None,
                    sync_events=None,pacing=None,duration_signals=None):
    ids=[b["beat_id"] for b in beats]
    order,cycle=topological_order(ids,dependencies)
    index={x:i for i,x in enumerate(order)}
    ordered=sorted(beats,key=lambda b:index.get(b["beat_id"],999))
    errors=["BEAT_DEPENDENCY_CYCLE"] if cycle else []
    if cycle:
        ordered=[]
    return {"schema_version":"5.40",
            "ordered_beats":ordered,
            "timing_constraints":timing_constraints or [],
            "sync_events":sync_events or [],
            "pacing":pacing or {},
            "duration_signals":duration_signals or {},
            "quality_gate":{"valid":not errors,"errors":errors}}
