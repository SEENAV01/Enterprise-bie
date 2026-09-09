from priority import rank
from deadline import deadline_state
from preemption import choose_preemption
from adaptive_scaling import scaling_decision

def decide(jobs,running_jobs,queue_depth,arrival_rate,service_rate,
           workers,now=0):
    ranked=rank(jobs,now)
    chosen=ranked[0] if ranked else None
    preempt=choose_preemption(running_jobs,chosen) if chosen else None
    scaling=scaling_decision(queue_depth,arrival_rate,service_rate,workers)
    deadlines=[{"job_id":j["job_id"],
                "state":deadline_state(j,j.get("elapsed",0))}
               for j in jobs]
    return {"ranked_job_ids":[j["job_id"] for j in ranked],
            "chosen_job_id":chosen["job_id"] if chosen else None,
            "preempt_job_id":preempt["job_id"] if preempt else None,
            "scaling":scaling,"deadline_states":deadlines}
