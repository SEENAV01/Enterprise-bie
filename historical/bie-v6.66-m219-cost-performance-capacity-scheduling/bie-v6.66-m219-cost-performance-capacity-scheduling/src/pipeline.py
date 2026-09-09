from cost_model import job_cost
from performance import performance_metrics
from capacity import capacity_forecast,required_workers
from scheduler import rank_jobs
from binpack import pack
from admission import admit
from optimization import optimization_plan

def build_performance_runtime():
    jobs=[
        {"job_id":"j1","cpu_seconds":10,"gpu_seconds":2,
         "memory_gb_seconds":20,"queue_seconds":3,
         "cpu":2,"memory":4,"gpu":1},
        {"job_id":"j2","cpu_seconds":6,"gpu_seconds":1,
         "memory_gb_seconds":10,"queue_seconds":1,
         "cpu":1,"memory":2,"gpu":1}
    ]
    rates={"cpu":1.0,"gpu":8.0,"memory":0.05}
    for j in jobs: j["estimated_cost"]=job_cost(j,rates)
    perf=performance_metrics(0,20,4,10,2,2)
    capacity=capacity_forecast(3,1,4)
    workers=required_workers(3,1,0.75)
    ranked=rank_jobs(jobs,{"gpu_load":0.2})
    packed=pack(jobs,{"cpu":4,"memory":8,"gpu":1})
    admissions=[admit(j,{"cpu":4,"memory":8,"gpu":1},
                       {"remaining_cost":100}) for j in jobs]
    plan=optimization_plan(jobs,4,30)
    return {"schema_version":"6.66","jobs":jobs,"performance":perf,
            "capacity_forecast":capacity,"required_workers":workers,
            "ranked_job_ids":[j["job_id"] for j in ranked],
            "packing":packed,"admission":admissions,
            "optimization_plan":plan,
            "optimization_gate":{"valid":(
                all(j["estimated_cost"]>0 for j in jobs)
                and perf["throughput_per_second"]>0
                and capacity["capacity"]==4
                and workers==4
                and len(packed["selected"])>=1
                and all(x["admitted"] for x in admissions)
                and plan["estimated_cost"]<=30
            ),"errors":[]}}
