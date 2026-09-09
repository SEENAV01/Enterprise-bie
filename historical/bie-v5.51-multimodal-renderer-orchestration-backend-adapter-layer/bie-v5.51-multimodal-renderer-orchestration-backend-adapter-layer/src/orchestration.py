def render_job(job_id,contract_ref,backend_ref=None,
               adapter_ref=None,priority=0,resources=None):
    return {"job_id":job_id,"contract_ref":contract_ref,
            "backend_ref":backend_ref,"adapter_ref":adapter_ref,
            "priority":priority,"resources":resources or {}}

def execution_result(job_id,status,artifacts=None,metrics=None,error=None):
    return {"job_id":job_id,"status":status,
            "artifacts":artifacts or {},"metrics":metrics or {},
            "error":error}
