def reqa_cycle(cycle_id, regeneration_job_id,
              qa_report_id, status, changed_refs=None):
    if status not in {"PASS","FAIL","REVIEW"}:
        raise ValueError("INVALID_REQA_STATUS")
    return {"cycle_id":cycle_id,"regeneration_job_id":regeneration_job_id,
            "qa_report_id":qa_report_id,"status":status,
            "changed_refs":changed_refs or []}

def passed(c):
    return c["status"]=="PASS"
