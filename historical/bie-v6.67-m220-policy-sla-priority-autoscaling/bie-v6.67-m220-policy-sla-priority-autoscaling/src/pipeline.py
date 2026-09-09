from policy import policy,validate
from slo import slo,compliance
from policy_engine import decide

def build_policy_runtime():
    p=policy("lesson-render","HIGH",120,True,3)
    jobs=[
      {"job_id":"j1","priority_class":"NORMAL","queued_at":0,"elapsed":50},
      {"job_id":"j2","priority_class":"CRITICAL","queued_at":10,
       "deadline_seconds":100,"elapsed":85},
      {"job_id":"j3","priority_class":"LOW","queued_at":0,"elapsed":20}
    ]
    running=[{"job_id":"r1","priority_class":"NORMAL","preemptible":True}]
    slo_def=slo("lesson_completion",0.95)
    slo_result=compliance(0.97,slo_def["target"])
    decision=decide(jobs,running,3,3,1,3,now=100)
    return {"schema_version":"6.67","policy":p,"jobs":jobs,
            "slo":slo_def,"slo_compliance":slo_result,
            "decision":decision,
            "policy_gate":{"valid":(
                validate(p) and slo_result["compliant"]
                and decision["chosen_job_id"]=="j2"
                and decision["preempt_job_id"]=="r1"
                and decision["scaling"]["action"]=="SCALE_OUT"
            ),"errors":[]}}
