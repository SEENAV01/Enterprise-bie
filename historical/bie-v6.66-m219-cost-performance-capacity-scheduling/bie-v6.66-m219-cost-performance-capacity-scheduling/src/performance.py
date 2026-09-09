def performance_metrics(start,end,queue_seconds=0,
                       cpu_seconds=0,gpu_seconds=0,items=1):
    wall=max(0,end-start)
    return {"wall_seconds":wall,"queue_seconds":queue_seconds,
            "execution_seconds":max(0,wall-queue_seconds),
            "throughput_per_second":items/wall if wall else 0,
            "cpu_utilization":cpu_seconds/wall if wall else 0,
            "gpu_utilization":gpu_seconds/wall if wall else 0}
