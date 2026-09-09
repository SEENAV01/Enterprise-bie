def resource_budget(cpu_seconds=None,memory_mb=None,
                   gpu_seconds=None,wall_seconds=None,
                   storage_mb=None,output_mb=None):
    return {"cpu_seconds":cpu_seconds,"memory_mb":memory_mb,
            "gpu_seconds":gpu_seconds,"wall_seconds":wall_seconds,
            "storage_mb":storage_mb,"output_mb":output_mb}

def budget_check(usage,budget):
    exceeded=[]
    for k,v in budget.items():
        if v is not None and usage.get(k,0)>v:
            exceeded.append(k)
    return {"allowed":not exceeded,"exceeded":exceeded}
