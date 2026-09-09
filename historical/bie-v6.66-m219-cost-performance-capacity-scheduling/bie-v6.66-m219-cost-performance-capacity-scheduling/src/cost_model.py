def estimate_cost(cpu_seconds=0,gpu_seconds=0,memory_gb_seconds=0,
                 rates=None):
    r=rates or {"cpu":1.0,"gpu":8.0,"memory":0.05}
    return (cpu_seconds*r["cpu"]+
            gpu_seconds*r["gpu"]+
            memory_gb_seconds*r["memory"])

def job_cost(job, rates=None):
    return estimate_cost(job.get("cpu_seconds",0),
                         job.get("gpu_seconds",0),
                         job.get("memory_gb_seconds",0),rates)
