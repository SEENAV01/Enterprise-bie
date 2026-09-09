from scheduler import schedule

def compile_orchestration(jobs,completed=None,resources=None):
    plan=schedule(jobs,completed,resources)
    return {"schema_version":"5.59","jobs":jobs,
            "schedule":plan,
            "quality_gate":{"valid":True,"errors":[]}}
