def regeneration_job(job_id, remediation_action_id,
                    target_refs, input_refs=None, attempt=1):
    return {"job_id":job_id,"remediation_action_id":remediation_action_id,
            "target_refs":target_refs,"input_refs":input_refs or [],
            "attempt":attempt,"status":"QUEUED"}

def valid(j):
    return bool(j["job_id"] and j["remediation_action_id"] and
                j["target_refs"] and j["attempt"] > 0)
