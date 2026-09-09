from jobs import runnable
from dag import validate_dag
from retry import retry_decision

def plan_runnable(jobs,completed):
    return [j for j in jobs if runnable(j,set(completed))]

def workflow_gate(jobs):
    return validate_dag(jobs)

def handle_failure(job_record,error_class):
    return retry_decision(job_record,error_class)
